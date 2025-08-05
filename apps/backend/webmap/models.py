from django.contrib.gis.db import models as gis_models
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Layer(models.Model):
    """
    Represents a map layer that visualizes geodata.
    Each layer belongs to a webmap and contains styling and temporal information.
    """
    LAYER_TYPE_CHOICES = [
        ('vector', 'Vector'),
        ('raster', 'Raster'),
        ('tile', 'Tile'),
        ('geojson', 'GeoJSON'),
    ]
    
    name = models.CharField(max_length=200, help_text="Display name of the layer")
    layer_type = models.CharField(
        max_length=50, 
        choices=LAYER_TYPE_CHOICES,
        default='vector',
        help_text="Type of layer (vector, raster, etc.)"
    )
    opacity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Layer opacity (0.0 to 1.0)"
    )
    style_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default JSON styling for all features in this layer. Can be overridden by individual feature attributes."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'layers'
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.layer_type})"


class GeoData(models.Model):
    """
    Represents the actual geographic dataset that belongs to a layer.
    Contains metadata about the data source and links to individual features.
    """
    layer = models.OneToOneField(
        Layer,
        on_delete=models.CASCADE,
        related_name='geodata',
        help_text="The layer that visualizes this geodata"
    )
    name = models.CharField(max_length=200, help_text="Name of the dataset")
    description = models.TextField(
        blank=True,
        help_text="Description of the geographic dataset"
    )
    source_url = models.URLField(
        blank=True,
        help_text="URL of the original data source"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'geodata'
        verbose_name = 'Geographic Data'
        verbose_name_plural = 'Geographic Data'
        
    def __str__(self):
        return f"{self.name} (Layer: {self.layer.name})"


class Feature(gis_models.Model):
    """
    Represents individual geographic features (points, lines, polygons) within a dataset.
    Uses GeoDjango's geometry field to store spatial data with PostGIS backend.
    """
    geodata = models.ForeignKey(
        GeoData,
        on_delete=models.CASCADE,
        related_name='features',
        help_text="The geodata collection this feature belongs to"
    )
    geometry = gis_models.GeometryField(
        help_text="Geometric representation (Point, LineString, Polygon, etc.)"
    )
    
    # Common fields for QGIS editing
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Feature name (shown in popups and labels)"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the feature"
    )
    
    # Style fields
    style_color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Feature color in hex format (e.g., #ff0000)"
    )
    style_opacity = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.0, message="Opacity must be at least 0.0"),
            MaxValueValidator(1.0, message="Opacity must be at most 1.0")
        ],
        help_text="Opacity (0.0 to 1.0), falls back to layer opacity"
    )
    style_weight = models.FloatField(
        null=True,
        blank=True,
        help_text="Line weight or border width in pixels"
    )
    
    # Original JSON field (renamed to _attributes)
    _attributes = models.JSONField(
        default=dict,
        null=True,  # Allow NULL in database
        blank=True,  # Allow empty in forms
        help_text="Additional properties in JSON format"
    )
    
    # Temporal properties
    time_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The time from which this feature is valid or visible."
    )
    time_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The time until which this feature is valid or visible."
    )
    zoom_range = models.CharField(
        max_length=50,
        blank=True,
        help_text="Zoom level range where feature is visible (e.g., '5-15')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'features'
        indexes = [
            gis_models.Index(fields=['geometry']),  # Spatial index
            models.Index(fields=['geodata', 'created_at']),
            models.Index(fields=['time_from', 'time_to']), # Index for temporal queries
            models.Index(fields=['name']),  # For name searches
        ]
        
    def __init__(self, *args, **kwargs):
        # Handle both old 'attributes' and new '_attributes' during transition
        if 'attributes' in kwargs and '_attributes' not in kwargs:
            kwargs['_attributes'] = kwargs.pop('attributes')
        super().__init__(*args, **kwargs)
        
        # Ensure _attributes is a dict
        if self._attributes is None:
            self._attributes = {}
            
        # Initialize fields from _attributes on first access
        if not hasattr(self, '_initialized_from_attrs'):
            self._init_from_attributes()
    
    def _init_from_attributes(self):
        """Initialize fields from _attributes JSON."""
        if not self._attributes:
            return
            
        # Set direct fields
        self.name = self._attributes.get('name', self.name)
        self.description = self._attributes.get('description', self.description)
        
        # Set style fields
        style = self._attributes.get('style', {})
        self.style_color = style.get('color', self.style_color)
        self.style_opacity = style.get('opacity', self.style_opacity)
        self.style_weight = style.get('weight', self.style_weight)
        
        # Mark as initialized
        self._initialized_from_attrs = True
    
    @property
    def attributes(self):
        """Get all attributes as a dict, including style properties."""
        attrs = self._attributes.copy()
        
        # Update with direct fields
        if self.name:
            attrs['name'] = self.name
        if self.description:
            attrs['description'] = self.description
            
        # Update style
        style = attrs.get('style', {})
        if self.style_color:
            style['color'] = self.style_color
        if self.style_opacity is not None:
            style['opacity'] = self.style_opacity
        if self.style_weight is not None:
            style['weight'] = self.style_weight
            
        if style:  # Only add style if there are any properties
            attrs['style'] = style
            
        return attrs
    
    @attributes.setter
    def attributes(self, value):
        """Set attributes from a dict, updating relevant fields."""
        if not isinstance(value, dict):
            return
            
        self._attributes = value
        self._init_from_attributes()
    
    def save(self, *args, **kwargs):
        # Ensure _attributes is always a dict
        if self._attributes is None or not isinstance(self._attributes, dict):
            self._attributes = {}
            
        # Update _attributes with current field values
        attrs = self._attributes.copy()
        
        # Update direct fields
        if self.name:
            attrs['name'] = self.name
        if self.description:
            attrs['description'] = self.description
            
        # Update style
        style = attrs.get('style', {})
        if self.style_color:
            style['color'] = self.style_color
        if self.style_opacity is not None:
            style['opacity'] = self.style_opacity
        if self.style_weight is not None:
            style['weight'] = self.style_weight
            
        if style:  # Only add style if there are any properties
            attrs['style'] = style
            
        self._attributes = attrs
        super().save(*args, **kwargs)
    
    def __str__(self):
        geom_type = self.geometry.geom_type if self.geometry else "Unknown"
        name = self.name or f"{geom_type} feature"
        return f"{name} in {self.geodata.name}"
    
    def get_geometry_type(self):
        """Return the geometry type as a string."""
        if self.geometry:
            return self.geometry.geom_type
        return None
    
    def get_attributes_display(self):
        """Return formatted attributes for display."""
        attrs = self.attributes
        if not attrs:
            return "No attributes"
            
        # Format for display, excluding internal fields
        display_attrs = {
            k: v for k, v in attrs.items()
            if not k.startswith('_') and k != 'style'
        }
        
        # Add style properties at the top level for visibility
        if 'style' in attrs:
            display_attrs.update({
                f"Style: {k}": v 
                for k, v in attrs['style'].items()
            })
            
        return json.dumps(display_attrs, indent=2, default=str)
