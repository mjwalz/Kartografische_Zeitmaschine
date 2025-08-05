from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'layers', views.LayerViewSet, basename='layer')
router.register(r'geodata', views.GeoDataViewSet, basename='geodata')
router.register(r'features', views.FeatureViewSet, basename='feature')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
