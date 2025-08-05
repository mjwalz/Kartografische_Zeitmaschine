from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, LineString, Polygon, MultiLineString
from datetime import date, datetime, timedelta
from webmap.models import Layer, GeoData, Feature
from django.utils import timezone
import json
import os
from django.contrib.gis.geos import GEOSGeometry
import random

# Helper function to generate random dates
def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


class Command(BaseCommand):
    help = 'Loads sample data for Germany into the database, including layers for cities, rivers, states, and more.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting existing data...")
        Feature.objects.all().delete()
        GeoData.objects.all().delete()
        Layer.objects.all().delete()

        self.stdout.write("Loading Germany sample data...")
        self.create_city_layer()
        self.create_rivers_layer()
        self.create_states_layer()
        self.create_transport_layer()
        self.create_historical_layer()
        self.create_raster_layer()
        self.create_satellite_layer()
        self.stdout.write(self.style.SUCCESS('Successfully loaded all sample data.'))

    def create_city_layer(self):
        self.stdout.write("Creating major cities layer...")
        layer = Layer.objects.create(
            name="German Major Cities",
            layer_type="vector",
            opacity=0.9,
            style_config={
                "fillColor": "#FF6B6B",
                "color": "#C92A2A",
                "weight": 2,
                "radius": 8,
                "fillOpacity": 0.7
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="Major Cities of Germany",
            description="Population centers and major cities in Germany.",
            source_url="https://www.destatis.de/"
        )
        
        # Define city data with explicit fields
        cities_data = [
            {
                "name": "Berlin", 
                "geometry": Point(13.4050, 52.5200), 
                "description": "Capital and largest city of Germany",
                "style_color": "#C92A2A",
                "style_opacity": 0.9,
                "style_weight": 2,
                "time_from": date(1237, 1, 1),  # First documented mention
                "time_to": None,  # Still exists
                "attributes": {
                    "population": 3669491, 
                    "state": "Berlin", 
                    "type": "capital", 
                    "population_year": 2020,
                    "elevation": 34,
                    "timezone": "CET"
                }
            },
            {
                "name": "Munich", 
                "geometry": Point(11.5820, 48.1351), 
                "description": "Capital of Bavaria and third largest city in Germany",
                "style_color": "#D6336C",
                "style_opacity": 0.85,
                "style_weight": 2,
                "time_from": date(1158, 1, 1),  # First documented mention
                "time_to": None,
                "attributes": {
                    "population": 1484226, 
                    "state": "Bavaria", 
                    "type": "city", 
                    "population_year": 2020,
                    "elevation": 519,
                    "famous_for": "Oktoberfest, BMW, Allianz Arena"
                }
            },
            {
                "name": "Hamburg", 
                "geometry": Point(9.9937, 53.5511), 
                "description": "Second largest city in Germany and a major port city.",
                "style_color": "#15AABF",
                "style_opacity": 0.9,
                "style_weight": 2,
                "time_from": date(834, 1, 1),  # First fortified castle
                "time_to": None,
                "attributes": {
                    "population": 1906411, 
                    "state": "Hamburg", 
                    "type": "city", 
                    "population_year": 2020,
                    "famous_for": "Port of Hamburg, Speicherstadt, Elbphilharmonie"
                }
            },
            {
                "name": "Cologne", 
                "geometry": Point(6.9603, 50.9375), 
                "description": "Fourth largest city, known for its cathedral and Roman history.",
                "style_color": "#BE4BDB",
                "style_opacity": 0.85,
                "style_weight": 2,
                "time_from": date(50, 1, 1),  # Founded as a Roman colony
                "time_to": None,
                "attributes": {
                    "population": 1087863, 
                    "state": "North Rhine-Westphalia", 
                    "type": "city", 
                    "population_year": 2020,
                    "famous_for": "Cologne Cathedral, Eau de Cologne, Carnival"
                }
            },
            {
                "name": "Frankfurt am Main", 
                "geometry": Point(8.6821, 50.1109), 
                "description": "Major financial hub and home to the European Central Bank.",
                "style_color": "#4C6EF5",
                "style_opacity": 0.9,
                "style_weight": 2,
                "time_from": date(794, 1, 1),  # First mentioned
                "time_to": None,
                "attributes": {
                    "population": 753056, 
                    "state": "Hesse", 
                    "type": "financial_center", 
                    "population_year": 2020,
                    "famous_for": "Skyscrapers, Frankfurt Stock Exchange, Goethe"
                }
            }
        ]
        
        for city in cities_data:
            # Create feature with explicit fields
            feature = Feature(
                geodata=geodata,
                geometry=city['geometry'],
                name=city['name'],
                description=city['description'],
                style_color=city['style_color'],
                style_opacity=city['style_opacity'],
                style_weight=city['style_weight'],
                time_from=city['time_from'],
                time_to=city['time_to']
            )
            
            # Set attributes (will be stored in _attributes)
            feature.attributes = city['attributes']
            feature.save()

    def create_rivers_layer(self):
        self.stdout.write("Creating rivers layer...")
        layer = Layer.objects.create(
            name="Major German Rivers",
            layer_type="vector",
            opacity=0.8,
            style_config={
                "color": "#1E88E5",
                "weight": 4,
                "opacity": 0.8
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="Major Rivers of Germany",
            description="Major rivers flowing through Germany.",
            source_url="https://www.umweltbundesamt.de/"
        )
        
        # Define river data with explicit fields
        rivers_data = [
            {
                "name": "Rhine", 
                "geometry": LineString([(6.1566, 50.9413), (7.5886, 50.3569), (8.2398, 49.9929), (8.4034, 49.9929), (8.4679, 49.7200)]),
                "description": "One of the major European rivers, flowing through Switzerland, Germany, and the Netherlands.",
                "style_color": "#1E88E5",
                "style_opacity": 0.8,
                "style_weight": 4,
                "time_from": None,  # Rivers are considered permanent features
                "time_to": None,
                "attributes": {
                    "length_km": 1230, 
                    "basin_area": 185000, 
                    "countries": ["Germany", "Switzerland", "France", "Netherlands"],
                    "tributaries": ["Moselle", "Main", "Neckar", "Ruhr"],
                    "source": "Swiss Alps",
                    "mouth": "North Sea"
                }
            },
            {
                "name": "Danube", 
                "geometry": LineString([(10.0000, 48.1000), (11.6000, 48.5167), (12.9333, 48.5667), (13.3833, 48.7667)]),
                "description": "Second longest river in Europe, flowing through 10 countries.",
                "style_color": "#1976D2",
                "style_opacity": 0.85,
                "style_weight": 5,
                "time_from": None,
                "time_to": None,
                "attributes": {
                    "length_km": 2850, 
                    "basin_area": 801463, 
                    "countries": ["Germany", "Austria", "Slovakia", "Hungary", "Croatia", "Serbia", "Romania", "Bulgaria", "Moldova", "Ukraine"],
                    "tributaries": ["Inn", "Drava", "Tisza", "Sava", "Morava"],
                    "source": "Black Forest, Germany",
                    "mouth": "Black Sea"
                }
            },
        ]
        
        for river in rivers_data:
            # Create feature with explicit fields
            feature = Feature(
                geodata=geodata,
                geometry=river['geometry'],
                name=river['name'],
                description=river['description'],
                style_color=river['style_color'],
                style_opacity=river['style_opacity'],
                style_weight=river['style_weight'],
                time_from=river['time_from'],
                time_to=river['time_to']
            )
            
            # Set attributes (will be stored in _attributes)
            feature.attributes = river['attributes']
            feature.save()

    def create_states_layer(self):
        self.stdout.write("Creating states layer from GeoJSON...")
        
        # Path to the local GeoJSON file
        # https://github.com/isellsoap/deutschlandGeoJSON/blob/main/2_bundeslaender/4_niedrig.geo.json
        file_path = os.path.join(os.path.dirname(__file__), '4_niedrig.json')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'GeoJSON file not found at: {file_path}'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Failed to parse GeoJSON file: {file_path}'))
            return

        layer = Layer.objects.create(
            name="German States (from GeoJSON)",
            layer_type="vector",
            opacity=0.7,
            style_config={
                "fillColor": "#1f78b4",
                "color": "#a6cee3",
                "weight": 1,
                "fillOpacity": 0.4
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="German Federal States",
            description="The 16 federal states of Germany, loaded from deutschlandGeoJSON.",
            source_url="https://github.com/isellsoap/deutschlandGeoJSON"
        )

        for feature_data in geojson_data['features']:
            properties = feature_data['properties']
            geom_data = feature_data['geometry']

            # Create a GEOS-compatible geometry object
            try:
                geom = GEOSGeometry(json.dumps(geom_data))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skipping feature due to invalid geometry: {properties.get('NAME_2', 'Unknown')}"))
                continue

            # Create the feature
            state_name = properties.get('name', 'Unnamed State')
            state_type = properties.get('type', 'State')
            state_id = properties.get('id', '')
            
            Feature.objects.create(
                geodata=geodata,
                geometry=geom,
                name=state_name,
                description=f"Federal state of {state_name}. Type: {state_type}.",
                attributes={
                    'type': state_type,
                    'state_id': state_id,
                    'country': 'Germany',
                    'varname': state_id  # Using the id (e.g., 'DE-BW') as varname
                }
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(geojson_data["features"])} state features.'))

    def create_transport_layer(self):
        self.stdout.write("Creating transport layer...")
        layer = Layer.objects.create(
            name="Transport Network",
            layer_type="vector",
            opacity=0.8,
            style_config={
                "color": "#F76707",
                "weight": 2,
                "dashArray": "5, 5"
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="German Transport Network",
            description="Major transport routes in Germany.",
            source_url="https://www.bmvi.de/"
        )
        
        # Define transport data with explicit fields
        transport_data = [
            {
                "name": "A1", 
                "geometry": LineString([(6.1, 50.9), (7.0, 51.0), (7.6, 51.4), (8.3, 52.1), (8.8, 53.1)]),
                "description": "Autobahn 1, runs from Saarbrücken in the southwest to Lübeck in the north.",
                "style_color": "#F76707",
                "style_opacity": 0.8,
                "style_weight": 3,
                "time_from": date(1965, 1, 1),  # Approximate completion date
                "time_to": None,
                "attributes": {
                    "type": "highway",
                    "length_km": 748,
                    "start_point": "Saarbrücken",
                    "end_point": "Heiligenhafen",
                    "lanes": 4,
                    "speed_limit": "None (recommended 130 km/h)",
                    "toll": False
                }
            },
            {
                "name": "A2", 
                "geometry": LineString([(6.1, 50.8), (7.4, 51.5), (8.3, 52.3), (9.7, 52.3), (11.0, 52.1)]),
                "description": "Autobahn 2, connects the Ruhr area with Berlin.",
                "style_color": "#E8590C",
                "style_opacity": 0.8,
                "style_weight": 3,
                "time_from": date(1965, 1, 1),
                "time_to": None,
                "attributes": {
                    "type": "highway",
                    "length_km": 486,
                    "start_point": "Oberhausen",
                    "end_point": "Werder (Havel)",
                    "lanes": 4,
                    "speed_limit": "None (recommended 130 km/h)",
                    "toll": False
                }
            },
            {
                "name": "ICE Line", 
                "geometry": LineString([(6.9, 50.9), (7.5, 50.3), (8.6, 49.9), (9.2, 48.8), (10.9, 48.4)]),
                "description": "High-speed rail line connecting Cologne to Munich via Frankfurt and Stuttgart.",
                "style_color": "#5F3DC4",
                "style_opacity": 0.8,
                "style_weight": 2,
                "style_dash_array": "5, 3",
                "time_from": date(1991, 5, 29),  # First ICE service
                "time_to": None,
                "attributes": {
                    "type": "rail",
                    "operator": "Deutsche Bahn",
                    "max_speed_kmh": 300,
                    "electrified": True,
                    "stations": ["Cologne", "Frankfurt Airport", "Stuttgart", "Augsburg", "Munich"],
                    "travel_time_minutes": 280
                }
            }
        ]
        
        for route in transport_data:
            # Create feature with explicit fields
            feature = Feature(
                geodata=geodata,
                geometry=route['geometry'],
                name=route['name'],
                description=route['description'],
                style_color=route['style_color'],
                style_opacity=route['style_opacity'],
                style_weight=route['style_weight'],
                time_from=route['time_from'],
                time_to=route['time_to']
            )
            
            # Set attributes (will be stored in _attributes)
            feature.attributes = route['attributes']
            feature.save()

    def create_historical_layer(self):
        self.stdout.write("Creating historical sites layer...")
        layer = Layer.objects.create(
            name="Historical Sites",
            layer_type="vector",
            opacity=0.9,
            style_config={
                "fillColor": "#F59F00",
                "color": "#E67700",
                "weight": 1,
                "radius": 6,
                "fillOpacity": 0.7
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="Historical Landmarks",
            description="Important historical sites and landmarks in Germany.",
            source_url="https://www.unesco.de/"
        )
        
        # Define historical sites with explicit fields
        sites_data = [
            {
                "name": "Cologne Cathedral", 
                "geometry": Point(6.9573, 50.9413), 
                "description": "A masterpiece of Gothic architecture and a UNESCO World Heritage Site.",
                "style_color": "#F59F00",
                "style_opacity": 0.9,
                "style_weight": 1,
                "time_from": date(1248, 1, 1),  # Construction started
                "time_to": None,  # Still standing
                "attributes": {
                    "type": "cathedral", 
                    "built": 1248, 
                    "completed": 1880,  # Completion of towers
                    "height_m": 157.4,
                    "unesco": True,
                    "visitors_per_year": 6000000,
                    "architectural_style": "Gothic"
                }
            },
            {
                "name": "Brandenburg Gate", 
                "geometry": Point(13.3777, 52.5163), 
                "description": "Neoclassical monument and one of the most famous landmarks of Germany.",
                "style_color": "#E67700",
                "style_opacity": 0.9,
                "style_weight": 1,
                "time_from": date(1791, 1, 1),  # Completion
                "time_to": None,
                "attributes": {
                    "type": "monument", 
                    "built": 1791, 
                    "height_m": 26,
                    "significance": "Symbol of German unity and European history",
                    "architect": "Carl Gotthard Langhans",
                    "architectural_style": "Neoclassical",
                    "events": ["Napoleonic Wars", "Cold War", "Fall of the Berlin Wall"]
                }
            },
        ]
        
        for site in sites_data:
            # Create feature with explicit fields
            feature = Feature(
                geodata=geodata,
                geometry=site['geometry'],
                name=site['name'],
                description=site['description'],
                style_color=site['style_color'],
                style_opacity=site['style_opacity'],
                style_weight=site['style_weight'],
                time_from=site['time_from'],
                time_to=site['time_to']
            )
            
            # Set attributes (will be stored in _attributes)
            feature.attributes = site['attributes']
            feature.save()

    def create_raster_layer(self):
        self.stdout.write("Creating raster layer...")
        layer = Layer.objects.create(
            name="Elevation Model",
            layer_type="raster",
            opacity=0.7,
            style_config={
                "minZoom": 0,
                "maxZoom": 18,
                "opacity": 0.7,
                "colorRamp": "terrain",
                "colorScale": "quantile",
                "classes": 10
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="Digital Elevation Model (DEM)",
            description="Elevation data for Germany with 30m resolution.",
            source_url="https://www.bkg.bund.de/"
        )
        
        # Create a point feature representing the raster data source
        feature = Feature(
            geodata=geodata,
            geometry=Point(10.5, 51.2),  # Rough center of Germany
            name="DEM Coverage Area",
            description="Coverage area for the Digital Elevation Model of Germany",
            style_color="#555555",
            style_opacity=0.7,
            style_weight=1,
            time_from=date(2000, 1, 1),  # Approximate data collection start
            time_to=None
        )
        
        # Set attributes for the raster data
        feature.attributes = {
            "data_type": "raster",
            "resolution_meters": 30,
            "coverage": "Germany",
            "data_format": "GeoTIFF",
            "vertical_datum": "DHHN2016",
            "provider": "Federal Agency for Cartography and Geodesy (BKG)",
            "update_frequency": "5 years",
            "license": "Data licence Germany – attribution – version 2.0"
        }
        feature.save()

    def create_satellite_layer(self):
        self.stdout.write("Creating satellite imagery layer...")
        layer = Layer.objects.create(
            name="Satellite Imagery",
            layer_type="raster",
            opacity=1.0,
            style_config={
                "minZoom": 0,
                "maxZoom": 19,
                "opacity": 1.0,
                "bands": ["B04", "B03", "B02"],  # True color composite
                "gamma": 1.0,
                "enhance": True
            }
        )
        geodata = GeoData.objects.create(
            layer=layer,
            name="Sentinel-2 Satellite Imagery",
            description="High-resolution satellite imagery from the Copernicus Sentinel-2 mission.",
            source_url="https://www.sentinel-hub.com/"
        )
        
        # Create a point feature representing the satellite data source
        feature = Feature(
            geodata=geodata,
            geometry=Point(10.5, 51.2),  # Rough center of Germany
            name="Sentinel-2 Coverage",
            description="Coverage area for Sentinel-2 satellite imagery",
            style_color="#2196F3",
            style_opacity=0.8,
            style_weight=1,
            time_from=date(2015, 6, 23),  # Launch of Sentinel-2A
            time_to=None
        )
        
        # Set attributes for the satellite data
        feature.attributes = {
            "data_type": "satellite_imagery",
            "satellite": "Sentinel-2",
            "resolution_meters": 10,  # For visible and NIR bands
            "temporal_coverage": "2015-present",
            "revisit_time_days": 5,  # With two satellites
            "provider": "European Space Agency (ESA)",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "processing_level": "Level-2A (Surface Reflectance)",
            "spectral_bands": [
                {"name": "Coastal Aerosol", "resolution_m": 60, "wavelength_nm": 443},
                {"name": "Blue", "resolution_m": 10, "wavelength_nm": 490},
                {"name": "Green", "resolution_m": 10, "wavelength_nm": 560},
                {"name": "Red", "resolution_m": 10, "wavelength_nm": 665},
                {"name": "Vegetation Red Edge", "resolution_m": 20, "wavelength_nm": 705},
                {"name": "Vegetation Red Edge", "resolution_m": 20, "wavelength_nm": 740},
                {"name": "Vegetation Red Edge", "resolution_m": 20, "wavelength_nm": 783},
                {"name": "NIR", "resolution_m": 10, "wavelength_nm": 842},
                {"name": "Narrow NIR", "resolution_m": 20, "wavelength_nm": 865},
                {"name": "Water Vapor", "resolution_m": 60, "wavelength_nm": 945},
                {"name": "SWIR", "resolution_m": 20, "wavelength_nm": 1610},
                {"name": "SWIR", "resolution_m": 20, "wavelength_nm": 2190}
            ]
        }
        feature.save()
