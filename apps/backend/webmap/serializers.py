from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Layer, GeoData, Feature


class GeoDataSerializer(serializers.ModelSerializer):
    """ Serializer for GeoData model. """
    class Meta:
        model = GeoData
        fields = ('id', 'name', 'description', 'source_url')


class LayerSerializer(serializers.ModelSerializer):
    """ Serializer for Layer model, including nested GeoData. """
    geodata = GeoDataSerializer(read_only=True)

    class Meta:
        model = Layer
        fields = ('id', 'name', 'layer_type', 'opacity', 'style_config', 'geodata')


class FeatureSerializer(GeoFeatureModelSerializer):
    """ 
    Serializes Feature instances into a GeoJSON-compatible format.
    Includes a dynamic `effective_style` field that merges layer and feature styles.
    """
    effective_style = serializers.SerializerMethodField()

    class Meta:
        model = Feature
        geo_field = "geometry"
        # These fields will be in the `properties` of the GeoJSON feature
        fields = (
            'id', 'name', 'description', 'geodata', 'attributes', 
            'time_from', 'time_to', 'zoom_range', 'effective_style',
            'style_color', 'style_opacity', 'style_weight'
        )
    
    def get_effective_style(self, obj):
        """Merges the layer's default style with the feature's override style."""
        layer_style = {}
        # Safely access nested style properties
        if hasattr(obj, 'geodata') and obj.geodata and hasattr(obj.geodata, 'layer') and obj.geodata.layer:
            layer_style = obj.geodata.layer.style_config or {}

        # Start with layer's style
        effective_style = layer_style.copy()

        # Override with explicit feature styles if they exist
        if obj.style_color:
            effective_style['color'] = obj.style_color
        if obj.style_opacity is not None:
            effective_style['opacity'] = obj.style_opacity
        if obj.style_weight is not None:
            effective_style['weight'] = obj.style_weight
        
        # For any other style properties in the feature's attributes (e.g., dashArray)
        feature_style_override = obj.attributes.get('style', {})
        effective_style.update(feature_style_override)

        return effective_style


class FeatureLayerSerializer(serializers.ModelSerializer):
    """ Serializer for a Layer with all its features, for API bulk endpoint. """
    features = serializers.SerializerMethodField()

    class Meta:
        model = Layer
        fields = ('id', 'name', 'layer_type', 'opacity', 'style_config', 'features')

    def get_features(self, obj):
        """Return a GeoJSON FeatureCollection of all features in this layer."""
        try:
            features = obj.geodata.features.all()
            # Use the FeatureSerializer to serialize each feature
            feature_serializer = FeatureSerializer(features, many=True, context=self.context)
            return {
                "type": "FeatureCollection",
                "features": feature_serializer.data
            }
        except GeoData.DoesNotExist:
            return {"type": "FeatureCollection", "features": []}
