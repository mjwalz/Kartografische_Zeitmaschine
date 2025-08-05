from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.core.management import call_command
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase
from .models import Layer, GeoData, Feature


class ModelTests(TestCase):

    def setUp(self):
        self.layer = Layer.objects.create(
            name="Test Layer",
            layer_type='vector'
        )
        self.geodata = GeoData.objects.create(name="Test GeoData", layer=self.layer)

    def test_feature_creation_with_explicit_fields(self):
        """Test that Feature attributes are correctly set from explicit fields."""
        feature = Feature.objects.create(
            geodata=self.geodata,
            geometry=Point(0, 0),
            name="Test Feature",
            style_color="#ff0000",
            style_opacity=0.8,
        )
        self.assertEqual(feature.name, "Test Feature")
        self.assertEqual(feature.style_color, "#ff0000")
        self.assertEqual(feature.style_opacity, 0.8)

    def test_attribute_property_sync(self):
        """Test that the 'attributes' property correctly reflects model fields."""
        feature = Feature.objects.create(
            geodata=self.geodata,
            geometry=Point(0, 0),
            name="Sync Test",
            _attributes={'source': 'manual'}
        )
        attributes = feature.attributes
        self.assertEqual(attributes['name'], 'Sync Test')
        self.assertEqual(attributes['source'], 'manual')


class APITests(APITestCase):

    def setUp(self):
        self.layer = Layer.objects.create(
            name="API Test Layer",
            layer_type='vector',
            style_config={'color': '#112233'}
        )
        self.geodata = GeoData.objects.create(name="API Test GeoData", layer=self.layer)
        self.feature = Feature.objects.create(
            geodata=self.geodata,
            name='API Test Feature',
            geometry=Point(13.4050, 52.5200),  # Berlin
            style_color='#ff0000'
        )

    def test_list_layers(self):
        """Ensure we can list layers."""
        url = reverse('layer-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'API Test Layer')

    def test_retrieve_feature(self):
        """Ensure we can retrieve a single feature."""
        url = reverse('feature-detail', kwargs={'pk': self.feature.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['properties']['name'], 'API Test Feature')

    def test_layer_data_endpoint(self):
        """Test the custom /layers/{id}/data/ endpoint."""
        url = reverse('layer-data', kwargs={'pk': self.layer.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'FeatureCollection')
        self.assertEqual(len(response.data['features']), 1)
        self.assertEqual(response.data['features'][0]['properties']['name'], 'API Test Feature')

    def test_feature_effective_style(self):
        """Test that the effective_style is correctly computed in the serializer."""
        # Create a feature without a color to test fallback
        feature_no_color = Feature.objects.create(
            geodata=self.geodata,
            name='Feature with no color',
            geometry=Point(13.4050, 52.5200)
        )

        url = reverse('layer-data', kwargs={'pk': self.layer.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        # Find the properties for each feature
        props_with_color = next(f['properties'] for f in response.data['features'] if f['properties']['name'] == 'API Test Feature')
        props_no_color = next(f['properties'] for f in response.data['features'] if f['properties']['name'] == 'Feature with no color')

        # Check that the feature's own style is used when present
        self.assertEqual(props_with_color['effective_style']['color'], '#ff0000')
        # Check that the layer's default style is used as a fallback
        self.assertEqual(props_no_color['effective_style']['color'], '#112233')


class ManagementCommandTests(TransactionTestCase):

    def setUp(self):
        # TransactionTestCase does not automatically clear the database, so we must manually
        # clear the data to ensure the management command can run on a clean slate.
        Feature.objects.all().delete()
        GeoData.objects.all().delete()
        Layer.objects.all().delete()

    def test_load_sample_data_command(self):
        """Test the load_germany_sample_data management command."""
        call_command('load_germany_sample_data')
        self.assertTrue(Layer.objects.filter(name="Major Cities").exists())
        self.assertTrue(Feature.objects.filter(name="Berlin").exists())
