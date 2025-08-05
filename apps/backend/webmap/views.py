from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_gis.filters import InBBoxFilter
from django.db.models import Prefetch
from .models import Layer, GeoData, Feature
from .serializers import LayerSerializer, GeoDataSerializer, FeatureSerializer, FeatureLayerSerializer


class LayerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows layers to be viewed or edited.
    """
    serializer_class = LayerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['layer_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    
    def get_queryset(self):
        return Layer.objects.all().order_by('name').select_related('geodata')

    @action(detail=True, url_path='data', renderer_classes=[JSONRenderer])
    def data(self, request, pk=None):
        layer = self.get_object()
        features = layer.geodata.features.all()
        serializer = FeatureSerializer(features, many=True, context={'request': request})
        feature_collection = {
            'type': 'FeatureCollection',
            'features': serializer.data
        }
        return Response(feature_collection)


class GeoDataViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows geographic datasets to be viewed or edited.
    """
    serializer_class = GeoDataSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['layer__id']
    search_fields = ['name', 'description', 'source_url']
    ordering_fields = ['name', 'created_at', 'updated_at']
    
    def get_queryset(self):
        return GeoData.objects.select_related('layer').order_by('name')


class FeatureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows geographic features to be viewed or edited.
    Supports spatial filtering using the 'in_bbox' parameter.
    Example: /api/features/?in_bbox=-180,-90,180,90
    A viewset for viewing and editing feature instances.
    Supports bounding box, temporal, and text search filters.
    """
    queryset = Feature.objects.select_related('geodata__layer').all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    bbox_filter_field = 'geometry'
    filter_backends = (InBBoxFilter, DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    
    filterset_fields = {
        'geodata__layer': ['exact'],
        'time_from': ['gte', 'lte', 'exact'], 
        'time_to': ['gte', 'lte', 'exact'],
    }
    
    search_fields = ['name', 'description', '_attributes']
    
    ordering_fields = ['created_at', 'updated_at', 'time_from', 'time_to']
