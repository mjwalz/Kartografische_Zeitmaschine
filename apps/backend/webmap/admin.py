from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
import json
from .models import Layer, GeoData, Feature

@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'layer_type', 'opacity', 'feature_count')
    list_filter = ('layer_type', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'feature_map_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'layer_type', 'opacity')
        }),
        ('Styling', {
            'fields': ('style_config',),
            'classes': ('collapse',),
        }),

        ('Map Preview', {
            'fields': ('feature_map_preview',),
            'classes': ('wide',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',)
        }
        js = ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',)
    
    def feature_count(self, obj):
        """Show the number of features in this layer"""
        try:
            count = obj.geodata.features.count()
            return f"{count} features"
        except:
            return "0 features"
    feature_count.short_description = 'Features'
    
    def feature_map_preview(self, obj):
        """Display a Leaflet map with all features for this layer"""
        if not obj.id:
            return "Save the layer first to see the map preview."
        
        try:
            # Get all features for this layer
            features = obj.geodata.features.all()
            if not features:
                return "No features to display."
            
            # Create GeoJSON for all features with their styles
            features_geojson = []
            for feature in features:
                if feature.geometry:
                    # Get the feature's style
                    feature_style = {}
                    
                    # Add direct style fields if they exist
                    if hasattr(feature, 'style_color') and feature.style_color:
                        feature_style['color'] = feature.style_color
                        feature_style['fillColor'] = feature.style_color
                    if hasattr(feature, 'style_opacity') and feature.style_opacity is not None:
                        feature_style['opacity'] = feature.style_opacity
                        feature_style['fillOpacity'] = feature.style_opacity
                    if hasattr(feature, 'style_weight') and feature.style_weight is not None:
                        feature_style['weight'] = feature.style_weight
                    
                    # Include any style from attributes
                    if hasattr(feature, 'attributes') and isinstance(feature.attributes, dict):
                        if 'style' in feature.attributes and isinstance(feature.attributes['style'], dict):
                            feature_style.update(feature.attributes['style'])
                    
                    feature_data = {
                        "type": "Feature",
                        "geometry": json.loads(feature.geometry.geojson),
                        "properties": {
                            "id": feature.id,
                            "attributes": feature.attributes or {},
                            "zoom_range": feature.zoom_range or "",
                            "style": feature_style  # Include the computed style
                        }
                    }
                    features_geojson.append(feature_data)
            
            if not features_geojson:
                return "No valid geometries to display."
            
            # Get style configuration
            style_config = obj.style_config or {}
            default_style = {
                "fillColor": "#3388ff",
                "color": "#3388ff",
                "weight": 2,
                "opacity": 0.8,
                "fillOpacity": 0.6,
                "radius": 8
            }
            style_config = {**default_style, **style_config}
            
            map_html = f'''
            <div id="layer-map-{obj.id}" style="height: 400px; width: 100%; border: 1px solid #ddd; margin: 10px 0;"></div>
            <p><strong>Layer:</strong> {obj.name} ({len(features_geojson)} features)</p>
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    // Check if map already exists and destroy it
                    if (window.layerMap{obj.id}) {{
                        window.layerMap{obj.id}.remove();
                    }}
                    
                    // Create new map
                    window.layerMap{obj.id} = L.map('layer-map-{obj.id}').setView([51.1657, 10.4515], 6);
                    
                    // Add tile layer
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    }}).addTo(window.layerMap{obj.id});
                    
                    // Add features
                    var features = {json.dumps(features_geojson)};
                    var layerStyle = {json.dumps(style_config)};

                    var featureGroup = L.geoJSON(features, {{
                        pointToLayer: function(feature, latlng) {{
                            // Get feature style from properties.style (not properties.attributes.style)
                            var featureStyle = feature.properties.style || {{}};
                            // Feature style overrides layer style
                            var finalStyle = {{...layerStyle, ...featureStyle}};
                            return L.circleMarker(latlng, {{
                                radius: finalStyle.radius || 8,
                                fillColor: finalStyle.fillColor || "#3388ff",
                                color: finalStyle.color || "#3388ff",
                                weight: finalStyle.weight || 2,
                                opacity: finalStyle.opacity || 0.8,
                                fillOpacity: finalStyle.fillOpacity || 0.6
                            }});
                        }},
                        style: function(feature) {{
                            // Get feature style from properties.style (not properties.attributes.style)
                            var featureStyle = feature.properties.style || {{}};
                            // Feature style overrides layer style
                            var finalStyle = {{...layerStyle, ...featureStyle}};
                            return {{
                                color: finalStyle.color || "#3388ff",
                                weight: finalStyle.weight || 2,
                                opacity: finalStyle.opacity || 0.8,
                                fillColor: finalStyle.fillColor || "#3388ff",
                                fillOpacity: finalStyle.fillOpacity || 0.6
                            }};
                        }},
                        onEachFeature: function(feature, layer) {{
                            var popupContent = "<strong>Feature ID:</strong> " + feature.properties.id;
                            if (feature.properties.attributes && Object.keys(feature.properties.attributes).length > 0) {{
                                popupContent += "<br><strong>Attributes:</strong><br>";
                                for (var key in feature.properties.attributes) {{
                                    popupContent += key + ": " + feature.properties.attributes[key] + "<br>";
                                }}
                            }}
                            layer.bindPopup(popupContent);
                        }}
                    }}).addTo(window.layerMap{obj.id});
                    
                    // Fit map to features
                    if (featureGroup.getBounds().isValid()) {{
                        window.layerMap{obj.id}.fitBounds(featureGroup.getBounds(), {{padding: [20, 20]}});
                    }}
                }});
            </script>
            '''
            
            return mark_safe(map_html)
            
        except Exception as e:
            return f"Error loading map: {str(e)}"
    
    feature_map_preview.short_description = 'Layer Features Map'


@admin.register(GeoData)
class GeoDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'layer_name', 'source_url', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'source_url')
    readonly_fields = ('created_at', 'updated_at')
    
    def layer_name(self, obj):
        return obj.layer.name
    layer_name.short_description = 'Layer'


@admin.register(Feature)
class FeatureAdmin(GISModelAdmin):
    list_display = ('name', 'geodata_name', 'geometry_type', 'time_from', 'time_to', 'created_at')
    list_filter = ('geodata__layer__name', 'created_at', 'time_from', 'time_to')
    search_fields = ('name', 'description', '_attributes')
    readonly_fields = ('created_at', 'updated_at', 'geometry_type', 'get_attributes_display')

    fieldsets = (
        ('Core Information', {
            'fields': ('geodata', 'geometry', 'name', 'description')
        }),
        ('Styling (Overrides Layer Default)', {
            'fields': ('style_color', 'style_opacity', 'style_weight'),
            'classes': ('collapse',)
        }),
        ('Temporal & Zoom', {
            'fields': ('time_from', 'time_to', 'zoom_range'),
            'classes': ('collapse',)
        }),
        ('Additional Attributes (Read-Only)', {
            'fields': ('get_attributes_display', '_attributes'),
            'classes': ('collapse', 'wide'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def geodata_name(self, obj):
        return obj.geodata.name
    geodata_name.short_description = 'GeoData'
    geodata_name.admin_order_field = 'geodata__name'

    def geometry_type(self, obj):
        return obj.get_geometry_type()
    geometry_type.short_description = 'Geometry Type'

    def get_attributes_display(self, obj):
        """Show formatted attributes for display."""
        return format_html("<pre>{}</pre>", obj.get_attributes_display())
    get_attributes_display.short_description = 'All Attributes (Computed)'


# SpatialFeature model has been replaced by the new Layer/GeoData/Feature models
