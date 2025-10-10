import json
import random
import uuid
from datetime import datetime, timedelta
import os
from faker import Faker
import math

fake = Faker()

# Create output directory
os.makedirs('fiware_iot_data', exist_ok=True)

# Smart city districts and locations
DISTRICTS = ["Central", "North", "South", "East", "West", "Downtown", "Uptown", "Riverside", "Harbor", "University", 
             "Financial", "Historic", "Industrial", "Residential", "Shopping", "Cultural", "Government", "Park", 
             "Station", "Airport"]

BUILDING_TYPES = ["Residential", "Commercial", "Industrial", "Government", "Hospital", "School", "Mall", "Hotel", 
                  "Office", "Warehouse", "Apartment", "University", "Stadium", "Museum"]

def generate_location(district=None):
    """Generate realistic geo coordinates within a smart city"""
    base_lat, base_lon = 52.5200, 13.4050  # Berlin center
    if district:
        # Add some variance based on district index for consistency
        district_index = DISTRICTS.index(district) if district in DISTRICTS else random.randint(0, len(DISTRICTS)-1)
        variance = 0.01 * (district_index + 1)
        lat = base_lat + random.uniform(-variance, variance)
        lon = base_lon + random.uniform(-variance, variance)
    else:
        lat = base_lat + random.uniform(-0.5, 0.5)
        lon = base_lon + random.uniform(-0.5, 0.5)
    
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}

def generate_timestamp(hours_back=720):  # Default 30 days back
    """Generate realistic timestamps"""
    minutes_back = int(hours_back * 60)
    base_time = datetime.now() - timedelta(minutes=random.randint(0, minutes_back))
    return base_time.strftime("%Y-%m-%dT%H:%M:%SZ")

# Enhanced entity templates with more smart city concepts
EXTENDED_ENTITY_TYPES = {
    "SmartMeter": {"count": 1500, "description": "Building energy consumption monitoring"},
    "Patient": {"count": 500, "description": "Healthcare patient monitoring"},
    "BikeStation": {"count": 400, "description": "Bike sharing system stations"},
    "OffStreetParking": {"count": 600, "description": "Smart parking facilities"},
    "Product": {"count": 800, "description": "Retail inventory tracking"},
    "Order": {"count": 1000, "description": "E-commerce transactions"},
    "AirQualityObserved": {"count": 800, "description": "Environmental air quality sensors"},
    "TrafficFlowObserved": {"count": 1200, "description": "Road traffic monitoring"},
    "WeatherObserved": {"count": 300, "description": "Meteorological stations"},
    "WaterQualityObserved": {"count": 200, "description": "Water system monitoring"},
    "WasteContainer": {"count": 800, "description": "Smart garbage bins with fill-level sensors"},
    "Streetlight": {"count": 2000, "description": "Intelligent street lighting system"},
    "NoiseLevelObserved": {"count": 400, "description": "Urban noise pollution monitoring"},
    "PublicTransportVehicle": {"count": 600, "description": "Buses, trams, and metro vehicles"},
    "EVChargingStation": {"count": 300, "description": "Electric vehicle charging points"},
    "Building": {"count": 1000, "description": "Smart building management systems"},
    "RiverLevelObserved": {"count": 150, "description": "River and flood monitoring"},
    "SoilMoistureSensor": {"count": 500, "description": "Agricultural and park irrigation sensors"},
    "SecurityCamera": {"count": 1200, "description": "Public safety camera network"},
    "PedestrianFlow": {"count": 700, "description": "Foot traffic monitoring in public spaces"},
    "SolarPanel": {"count": 600, "description": "Renewable energy generation monitoring"},
    "Drone": {"count": 200, "description": "Municipal drone fleet for various services"},
    "SmartBench": {"count": 300, "description": "Public benches with USB charging and WiFi"},
    "EmergencyVehicle": {"count": 150, "description": "Police, fire, and ambulance tracking"},
    "RetailFootfall": {"count": 400, "description": "Shopping district customer counting"},
    "Greenhouse": {"count": 100, "description": "Urban farming environment monitoring"},
    "ConstructionSite": {"count": 180, "description": "Building site safety and progress monitoring"},
    "SportsFacility": {"count": 120, "description": "Stadiums and recreational facilities"},
    "VendingMachine": {"count": 350, "description": "Smart retail vending machines"},
    "PublicToilet": {"count": 200, "description": "Sanitation facility monitoring"},
    "Fountain": {"count": 80, "description": "Public water feature management"},
    "Bridge": {"count": 60, "description": "Infrastructure health monitoring"},
    "Elevator": {"count": 400, "description": "Building elevator status and usage"},
    "Ferry": {"count": 40, "description": "Water transportation monitoring"},
    "Tree": {"count": 800, "description": "Urban forestry health monitoring"},
    "Playground": {"count": 150, "description": "Recreational area usage monitoring"},
    "ArtInstallation": {"count": 100, "description": "Public art maintenance and interaction"},
    "Beehive": {"count": 50, "description": "Urban beekeeping environmental sensors"},
    "LitterBin": {"count": 600, "description": "Public litter bin status monitoring"}
}

# Original entity generators (from first script)
def generate_smart_meter_entity():
    district = random.choice(DISTRICTS)
    building_type = random.choice(BUILDING_TYPES)
    building_id = f"{building_type}_{random.randint(1, 1000)}"
    
    return {
        "id": f"urn:ngsi-ld:SmartMeter:{district}_{building_id}",
        "type": "SmartMeter",
        "building": {"type": "Text", "value": f"{district} {building_type} Building"},
        "electricityConsumption": {"type": "Number", "value": round(random.uniform(50, 500), 2)},
        "waterConsumption": {"type": "Number", "value": round(random.uniform(10, 200), 2)},
        "gasConsumption": {"type": "Number", "value": round(random.uniform(5, 100), 2)},
        "unit": {"type": "Text", "value": "kWh"},
        "timestamp": {"type": "DateTime", "value": generate_timestamp(24)},  # Last 24 hours
        "status": {"type": "Text", "value": random.choice(["active", "maintenance", "inactive"])},
        "district": {"type": "Text", "value": district}
    }

def generate_patient_entity():
    return {
        "id": f"urn:ngsi-ld:Patient:{str(uuid.uuid4())[:8]}",
        "type": "Patient",
        "name": {"type": "Text", "value": fake.name()},
        "age": {"type": "Number", "value": random.randint(1, 100)},
        "heartRate": {"type": "Number", "value": random.randint(60, 100)},
        "bloodPressure": {"type": "Text", "value": f"{random.randint(100, 140)}/{random.randint(60, 90)}"},
        "temperature": {"type": "Number", "value": round(random.uniform(36.0, 38.5), 1)},
        "oxygenSaturation": {"type": "Number", "value": round(random.uniform(95, 100), 1)},
        "lastCheckup": {"type": "DateTime", "value": generate_timestamp(720)},
        "ward": {"type": "Text", "value": random.choice(["Emergency", "ICU", "General", "Pediatrics", "Surgery"])}
    }

def generate_bike_station_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:BikeStation:{district}_{random.randint(1, 50)}",
        "type": "BikeStation",
        "name": {"type": "Text", "value": f"{district} Bike Station {random.randint(1, 20)}"},
        "location": {"type": "geo:json", "value": location},
        "availableBikes": {"type": "Number", "value": random.randint(0, 30)},
        "totalBikes": {"type": "Number", "value": 30},
        "availableDocks": {"type": "Number", "value": random.randint(0, 30)},
        "status": {"type": "Text", "value": random.choice(["operational", "maintenance", "closed"])},
        "dateModified": {"type": "DateTime", "value": generate_timestamp(6)}  # Last 6 hours
    }


def generate_soil_moisture_sensor():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return {
        "id": f"urn:ngsi-ld:SoilMoistureSensor:soil-sensor-{uuid.uuid4()}",
        "type": "SoilMoistureSensor",
        "soilMoisture": {
            "value": round(random.uniform(0, 100), 2),
            "type": "Number",
            "metadata": {
                "unitCode": {
                    "value": "P1",
                    "type": "Text"
                }
            }
        },
        "temperature": {
            "value": round(random.uniform(10, 35), 2),
            "type": "Number",
            "metadata": {
                "unitCode": {
                    "value": "CEL",
                    "type": "Text"
                }
            }
        },
        "location": {
            "value": location,
            "type": "geo:json",
            "metadata": {}
        },
        "dateCreated": {
            "value": datetime.now().isoformat(),
            "type": "DateTime"
        },
        "source": {
            "value": "Simulated Data",
            "type": "Text"
        },
        "description": {
            "value": "A sensor for measuring soil moisture and temperature.",
            "type": "Text"
        }
    }

def generate_river_level_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return {
        "id": f"urn:ngsi-ld:RiverLevelObserved:{district}_River_{random.randint(1, 100)}",
        "type": "RiverLevelObserved",
        "name": {"type": "Text", "value": f"River Level Sensor in {district}"},
        "location": {"type": "geo:json", "value": location},
        "level": {"type": "Number", "value": round(random.uniform(0.5, 5.0), 2)},  # in meters
        "flowRate": {"type": "Number", "value": round(random.uniform(10, 500), 2)}, # in m^3/s
        "status": {"type": "Text", "value": random.choice(["normal", "high_alert", "low_flow"])},
        "timestamp": {"type": "DateTime", "value": generate_timestamp(1)},
        "district": {"type": "Text", "value": district}
    }

def generate_parking_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    total_spots = random.choice([50, 100, 200, 500])
    available_spots = random.randint(0, total_spots)
    
    status = "operational"
    if available_spots == 0:
        status = "full"
    elif available_spots / total_spots < 0.1:
        status = "almost_full"
    
    return {
        "id": f"urn:ngsi-ld:OffStreetParking:{district}_{random.randint(1, 20)}",
        "type": "OffStreetParking",
        "name": {"type": "Text", "value": f"{district} Parking Garage"},
        "description": {"type": "Text", "value": f"Parking facility in {district} district"},
        "address": {"type": "Text", "value": fake.address()},
        "location": {"type": "geo:json", "value": location},
        "availableSpotNumber": {"type": "Number", "value": available_spots},
        "totalSpotNumber": {"type": "Number", "value": total_spots},
        "occupancy": {"type": "Number", "value": round((total_spots - available_spots) / total_spots * 100, 2)},
        "status": {"type": "Text", "value": status},
        "dateModified": {"type": "DateTime", "value": generate_timestamp(2)}  # Last 2 hours
    }

def generate_air_quality_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:AirQualityObserved:{district}-Sensor-{random.randint(1, 50)}",
        "type": "AirQualityObserved",
        "location": {"type": "geo:json", "value": location},
        "dateObserved": {"type": "DateTime", "value": generate_timestamp(1)},  # Last hour
        "airQualityIndex": {"type": "Number", "value": random.randint(0, 100)},
        "pm10": {"type": "Number", "value": random.randint(5, 50)},
        "pm2_5": {"type": "Number", "value": random.randint(2, 35)},
        "co2": {"type": "Number", "value": random.randint(300, 600)},
        "no2": {"type": "Number", "value": round(random.uniform(10, 100), 2)},
        "o3": {"type": "Number", "value": round(random.uniform(20, 120), 2)},
        "source": {"type": "Text", "value": f"AQ-Sensor-{random.randint(1000, 9999)}"},
        "district": {"type": "Text", "value": district}
    }

def generate_traffic_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:TrafficFlowObserved:{district}-{random.randint(1, 100)}",
        "type": "TrafficFlowObserved",
        "location": {"type": "geo:json", "value": location},
        "dateObserved": {"type": "DateTime", "value": generate_timestamp(0.5)},  # Last 30 minutes
        "laneId": {"type": "Text", "value": f"Lane_{random.randint(1, 4)}"},
        "vehicleCount": {"type": "Number", "value": random.randint(0, 200)},
        "averageSpeed": {"type": "Number", "value": random.randint(0, 120)},
        "congestionLevel": {"type": "Text", "value": random.choice(["low", "medium", "high", "very_high"])},
        "district": {"type": "Text", "value": district}
    }

def generate_weather_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:WeatherObserved:{district}-Station-{random.randint(1, 20)}",
        "type": "WeatherObserved",
        "location": {"type": "geo:json", "value": location},
        "dateObserved": {"type": "DateTime", "value": generate_timestamp(0.5)},  # Last 30 minutes
        "temperature": {"type": "Number", "value": round(random.uniform(-10, 35), 1)},
        "humidity": {"type": "Number", "value": random.randint(30, 95)},
        "pressure": {"type": "Number", "value": random.randint(980, 1040)},
        "windSpeed": {"type": "Number", "value": round(random.uniform(0, 50), 1)},
        "windDirection": {"type": "Number", "value": random.randint(0, 360)},
        "precipitation": {"type": "Number", "value": round(random.uniform(0, 10), 1)},
        "district": {"type": "Text", "value": district}
    }

def generate_water_quality_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:WaterQualityObserved:{district}-Monitor-{random.randint(1, 30)}",
        "type": "WaterQualityObserved",
        "location": {"type": "geo:json", "value": location},
        "dateObserved": {"type": "DateTime", "value": generate_timestamp(2)},  # Last 2 hours
        "ph": {"type": "Number", "value": round(random.uniform(6.5, 8.5), 2)},
        "turbidity": {"type": "Number", "value": round(random.uniform(0.1, 10.0), 2)},
        "chlorine": {"type": "Number", "value": round(random.uniform(0.1, 5.0), 2)},
        "temperature": {"type": "Number", "value": round(random.uniform(5, 25), 1)},
        "conductivity": {"type": "Number", "value": random.randint(100, 1000)},
        "district": {"type": "Text", "value": district}
    }

def generate_product_entity():
    shops = ["ElectronicsHeaven", "FashionWorld", "HomeEssentials", "TechStore", "SuperMarket"]
    categories = ["Electronics", "Clothing", "Home", "Food", "Books", "Sports"]
    
    product_name = fake.word().capitalize() + " " + fake.word().capitalize()
    shop = random.choice(shops)
    price = round(random.uniform(5, 2000), 2)
    on_sale = random.choice([True, False])
    
    entity = {
        "id": f"urn:ngsi-ld:Product:{product_name.replace(' ', '_')}_{shop}",
        "type": "Product",
        "name": {"type": "Text", "value": product_name},
        "price": {"type": "Number", "value": price},
        "currency": {"type": "Text", "value": "EUR"},
        "onSale": {"type": "Boolean", "value": on_sale},
        "shop": {"type": "Text", "value": shop},
        "category": {"type": "Text", "value": random.choice(categories)},
        "dateModified": {"type": "DateTime", "value": generate_timestamp(168)}  # Last week
    }
    
    if on_sale:
        entity["salePrice"] = {"type": "Number", "value": round(price * random.uniform(0.5, 0.9), 2)}
    
    return entity

def generate_order_entity():
    return {
        "id": f"urn:ngsi-ld:Order:{str(uuid.uuid4())[:12]}",
        "type": "Order",
        "customerName": {"type": "Text", "value": fake.name()},
        "orderDate": {"type": "DateTime", "value": generate_timestamp(720)},
        "totalAmount": {"type": "Number", "value": round(random.uniform(10, 500), 2)},
        "currency": {"type": "Text", "value": "EUR"},
        "status": {"type": "Text", "value": random.choice(["pending", "confirmed", "shipped", "delivered", "cancelled"])},
        "items": {"type": "Number", "value": random.randint(1, 10)},
        "shippingAddress": {"type": "Text", "value": fake.address()}
    }

# New entity generators for extended types
def generate_waste_container_entity():
    container_types = ["General Waste", "Recycling", "Organic", "Plastic", "Paper", "Glass"]
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:WasteContainer:{district}_{random.randint(1, 200)}",
        "type": "WasteContainer",
        "name": {"type": "Text", "value": f"{district} {random.choice(container_types)} Bin"},
        "location": {"type": "geo:json", "value": location},
        "containerType": {"type": "Text", "value": random.choice(container_types)},
        "fillLevel": {"type": "Number", "value": random.randint(0, 100)},
        "temperature": {"type": "Number", "value": round(random.uniform(10, 45), 1)},
        "lastEmptied": {"type": "DateTime", "value": generate_timestamp(168)},  # Last week
        "status": {"type": "Text", "value": random.choice(["ok", "full", "maintenance", "vandalized"])},
        "district": {"type": "Text", "value": district}
    }

def generate_security_camera_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:SecurityCamera:{district}_{random.randint(1, 200)}",
        "type": "SecurityCamera",
        "cameraStatus": {"type": "Text", "value": random.choice(["active", "inactive", "maintenance", "offline"])},
        "resolution": {"type": "Text", "value": random.choice(["1080p", "4K", "720p"])},
        "lastRecording": {"type": "DateTime", "value": generate_timestamp(24)}, # Last 24 hours
        "location": {"type": "geo:json", "value": location},
        "district": {"type": "Text", "value": district}
    }


def generate_streetlight_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    light_types = ["LED", "Sodium", "Halogen", "Solar"]
    
    return {
        "id": f"urn:ngsi-ld:Streetlight:{district}_Light_{random.randint(1, 5000)}",
        "type": "Streetlight",
        "location": {"type": "geo:json", "value": location},
        "lightType": {"type": "Text", "value": random.choice(light_types)},
        "status": {"type": "Text", "value": random.choice(["on", "off", "dimmed", "maintenance"])},
        "illuminance": {"type": "Number", "value": random.randint(0, 500)},
        "powerConsumption": {"type": "Number", "value": round(random.uniform(10, 200), 2)},
        "lastMaintenance": {"type": "DateTime", "value": generate_timestamp(720)},  # Last month
        "brightnessLevel": {"type": "Number", "value": random.randint(0, 100)},
        "motionDetected": {"type": "Boolean", "value": random.choice([True, False])},
        "district": {"type": "Text", "value": district}
    }

def generate_noise_level_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    noise_sources = ["Traffic", "Construction", "Commercial", "Residential", "Entertainment"]
    
    return {
        "id": f"urn:ngsi-ld:NoiseLevelObserved:{district}_Sensor_{random.randint(1, 100)}",
        "type": "NoiseLevelObserved",
        "location": {"type": "geo:json", "value": location},
        "dateObserved": {"type": "DateTime", "value": generate_timestamp(1)},
        "noiseLevel": {"type": "Number", "value": round(random.uniform(30, 120), 1)},  # dB
        "noiseSource": {"type": "Text", "value": random.choice(noise_sources)},
        "frequencyAnalysis": {
            "type": "StructuredValue",
            "value": {
                "low": round(random.uniform(20, 60), 1),
                "mid": round(random.uniform(30, 80), 1),
                "high": round(random.uniform(40, 100), 1)
            }
        },
        "district": {"type": "Text", "value": district}
    }

def generate_public_transport_entity():
    vehicle_types = ["Bus", "Tram", "Metro", "Train", "Ferry"]
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:PublicTransportVehicle:{random.choice(vehicle_types)}_{random.randint(1000, 9999)}",
        "type": "PublicTransportVehicle",
        "vehicleType": {"type": "Text", "value": random.choice(vehicle_types)},
        "location": {"type": "geo:json", "value": location},
        "speed": {"type": "Number", "value": round(random.uniform(0, 80), 1)},
        "heading": {"type": "Number", "value": random.randint(0, 359)},
        "passengerCount": {"type": "Number", "value": random.randint(0, 200)},
        "capacity": {"type": "Number", "value": random.choice([50, 80, 120, 200])},
        "line": {"type": "Text", "value": f"Line {random.randint(1, 20)}"},
        "nextStop": {"type": "Text", "value": f"Stop {random.randint(1, 50)}"},
        "status": {"type": "Text", "value": random.choice(["in_service", "out_of_service", "maintenance"])},
        "timestamp": {"type": "DateTime", "value": generate_timestamp(0.1)}  # Last 6 minutes
    }

def generate_ev_charging_station_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    connector_types = ["Type2", "CCS", "CHAdeMO", "Tesla"]
    
    return {
        "id": f"urn:ngsi-ld:EVChargingStation:{district}_EV_{random.randint(1, 100)}",
        "type": "EVChargingStation",
        "name": {"type": "Text", "value": f"{district} EV Charging Station"},
        "location": {"type": "geo:json", "value": location},
        "connectorType": {"type": "Text", "value": random.choice(connector_types)},
        "voltage": {"type": "Number", "value": random.choice([230, 400])},
        "amperage": {"type": "Number", "value": random.choice([16, 32, 64])},
        "power": {"type": "Number", "value": round(random.uniform(7, 150), 1)},
        "status": {"type": "Text", "value": random.choice(["available", "charging", "out_of_order"])},
        "currentUser": {"type": "Text", "value": fake.name() if random.random() > 0.7 else "none"},
        "energyDelivered": {"type": "Number", "value": round(random.uniform(0, 1000), 2)},
        "district": {"type": "Text", "value": district}
    }

def generate_building_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    building_types = ["Residential", "Commercial", "Office", "Government", "Hospital", "School"]
    
    return {
        "id": f"urn:ngsi-ld:Building:{district}_Building_{random.randint(1, 500)}",
        "type": "Building",
        "name": {"type": "Text", "value": f"{district} {random.choice(building_types)} Building"},
        "location": {"type": "geo:json", "value": location},
        "buildingType": {"type": "Text", "value": random.choice(building_types)},
        "floors": {"type": "Number", "value": random.randint(1, 50)},
        "occupancy": {"type": "Number", "value": random.randint(0, 100)},
        "energyRating": {"type": "Text", "value": random.choice(["A++", "A+", "A", "B", "C", "D"])},
        "indoorTemperature": {"type": "Number", "value": round(random.uniform(18, 26), 1)},
        "indoorHumidity": {"type": "Number", "value": random.randint(30, 60)},
        "co2Level": {"type": "Number", "value": random.randint(400, 1200)},
        "district": {"type": "Text", "value": district}
    }

# Add more entity generators as needed (simplified for brevity)
def generate_solar_panel_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:SolarPanel:{district}_Solar_{random.randint(1, 300)}",
        "type": "SolarPanel",
        "location": {"type": "geo:json", "value": location},
        "powerOutput": {"type": "Number", "value": round(random.uniform(0, 5), 2)},
        "efficiency": {"type": "Number", "value": round(random.uniform(15, 22), 1)},
        "status": {"type": "Text", "value": random.choice(["active", "maintenance", "shaded"])},
        "district": {"type": "Text", "value": district}
    }

def generate_pedestrian_flow_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:PedestrianFlow:{district}_{random.randint(1, 200)}",
        "type": "PedestrianFlow",
        "pedestrianCount": {"type": "Number", "value": random.randint(0, 500)},
        "dateObserved": {"type": "DateTime", "value": generate_timestamp(1)}, # Last hour
        "location": {"type": "geo:json", "value": location},
        "description": {"type": "Text", "value": "A simulated pedestrian count at a specific location."},
        "district": {"type": "Text", "value": district}
    }


def generate_drone_entity():
    drone_types = ["Delivery", "Surveillance", "Mapping", "Emergency", "Agricultural"]
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:Drone:{random.choice(drone_types)}_{random.randint(100, 999)}",
        "type": "Drone",
        "droneType": {"type": "Text", "value": random.choice(drone_types)},
        "location": {"type": "geo:json", "value": location},
        "altitude": {"type": "Number", "value": round(random.uniform(10, 120), 1)},
        "batteryLevel": {"type": "Number", "value": random.randint(10, 100)},
        "status": {"type": "Text", "value": random.choice(["flying", "landed", "charging", "maintenance"])},
        "timestamp": {"type": "DateTime", "value": generate_timestamp(0.05)}
    }

# Simplified generators for remaining types (you can expand these)
def generate_smart_bench_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:SmartBench:{district}_Bench_{random.randint(1, 150)}",
        "type": "SmartBench",
        "location": {"type": "geo:json", "value": location},
        "batteryLevel": {"type": "Number", "value": random.randint(0, 100)},
        "occupancy": {"type": "Boolean", "value": random.choice([True, False])},
        "district": {"type": "Text", "value": district}
    }

def generate_emergency_vehicle_entity():
    vehicle_types = ["Ambulance", "Police", "Fire", "Rescue"]
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    
    return {
        "id": f"urn:ngsi-ld:EmergencyVehicle:{random.choice(vehicle_types)}_{random.randint(100, 999)}",
        "type": "EmergencyVehicle",
        "vehicleType": {"type": "Text", "value": random.choice(vehicle_types)},
        "location": {"type": "geo:json", "value": location},
        "status": {"type": "Text", "value": random.choice(["dispatched", "on_scene", "available", "maintenance"])},
        "timestamp": {"type": "DateTime", "value": generate_timestamp(0.1)}
    }

# Placeholder generators for remaining types (implement similarly)
def generate_retail_footfall_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("RetailFootfall", district, location)

def generate_greenhouse_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Greenhouse", district, location)

def generate_construction_site_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("ConstructionSite", district, location)

def generate_sports_facility_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("SportsFacility", district, location)

def generate_vending_machine_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("VendingMachine", district, location)

def generate_public_toilet_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("PublicToilet", district, location)

def generate_fountain_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Fountain", district, location)

def generate_bridge_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Bridge", district, location)

def generate_elevator_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Elevator", district, location)

def generate_ferry_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Ferry", district, location)

def generate_tree_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Tree", district, location)

def generate_playground_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Playground", district, location)

def generate_art_installation_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("ArtInstallation", district, location)

def generate_beehive_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("Beehive", district, location)

def generate_litter_bin_entity():
    district = random.choice(DISTRICTS)
    location = generate_location(district)
    return basic_entity("LitterBin", district, location)

def basic_entity(entity_type, district, location):
    """Generate a basic entity with common attributes"""
    return {
        "id": f"urn:ngsi-ld:{entity_type}:{district}_{random.randint(1, 100)}",
        "type": entity_type,
        "name": {"type": "Text", "value": f"{district} {entity_type}"},
        "location": {"type": "geo:json", "value": location},
        "status": {"type": "Text", "value": random.choice(["active", "inactive", "maintenance"])},
        "timestamp": {"type": "DateTime", "value": generate_timestamp(24)},
        "district": {"type": "Text", "value": district}
    }

# Entity generation functions mapping
GENERATORS = {
    "SmartMeter": generate_smart_meter_entity,
    "Patient": generate_patient_entity,
    "BikeStation": generate_bike_station_entity,
    "OffStreetParking": generate_parking_entity,
    "Product": generate_product_entity,
    "Order": generate_order_entity,
    "AirQualityObserved": generate_air_quality_entity,
    "TrafficFlowObserved": generate_traffic_entity,
    "WeatherObserved": generate_weather_entity,
    "WaterQualityObserved": generate_water_quality_entity,
    "SoilMoistureSensor":generate_soil_moisture_sensor,
    "RiverLevelObserved": generate_river_level_entity,
    "WasteContainer": generate_waste_container_entity,
    "Streetlight": generate_streetlight_entity,
    "NoiseLevelObserved": generate_noise_level_entity,
    "PublicTransportVehicle": generate_public_transport_entity,
    "EVChargingStation": generate_ev_charging_station_entity,
    "Building": generate_building_entity,
    "SolarPanel": generate_solar_panel_entity,
    "SecurityCamera": generate_security_camera_entity,
    "Drone": generate_drone_entity,
    "SmartBench": generate_smart_bench_entity,
    "EmergencyVehicle": generate_emergency_vehicle_entity,
    "RetailFootfall": generate_retail_footfall_entity,
    "Greenhouse": generate_greenhouse_entity,
    "ConstructionSite": generate_construction_site_entity,
    "SportsFacility": generate_sports_facility_entity,
    "VendingMachine": generate_vending_machine_entity,
    "PublicToilet": generate_public_toilet_entity,
    "PedestrianFlow": generate_pedestrian_flow_entity,
    "Fountain": generate_fountain_entity,
    "Bridge": generate_bridge_entity,
    "Elevator": generate_elevator_entity,
    "Ferry": generate_ferry_entity,
    "Tree": generate_tree_entity,
    "Playground": generate_playground_entity,
    "ArtInstallation": generate_art_installation_entity,
    "Beehive": generate_beehive_entity,
    "LitterBin": generate_litter_bin_entity,
}

def generate_entities(entity_type, count, batch_size=100):
    """Generate multiple entities of a specific type"""
    entities = []
    for i in range(count):
        entity = GENERATORS[entity_type]()
        entities.append(entity)
        
        # Save in batches to avoid memory issues
        if len(entities) >= batch_size:
            save_entities(entity_type, entities, i - batch_size + 1)
            entities = []
    
    # Save remaining entities
    if entities:
        save_entities(entity_type, entities, count - len(entities))

def save_entities(entity_type, entities, start_index):
    """Save entities to JSON files"""
    for i, entity in enumerate(entities):
        filename = f"fiware_iot_data/{entity_type}_{start_index + i + 1}.json"
        with open(filename, 'w') as f:
            json.dump([entity], f, indent=2)

def generate_all_extended_data():
    """Generate thousands of diverse IoT sensor data files"""
    print("Generating Comprehensive FIWARE Smart City IoT Data...")
    
    total_files = sum(entity_type["count"] for entity_type in EXTENDED_ENTITY_TYPES.values())
    print(f"Generating {total_files} NGSI-v2 compliant JSON files...")
    
    for entity_type, config in EXTENDED_ENTITY_TYPES.items():
        print(f"Generating {config['count']} {entity_type} entities...")
        generate_entities(entity_type, config["count"])
    
    print(f"Data generation complete! {total_files} files created in 'fiware_iot_data' directory.")

def create_comprehensive_metadata():
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_entities": sum(entity_type["count"] for entity_type in EXTENDED_ENTITY_TYPES.values()),
        "entity_distribution": {k: v["count"] for k, v in EXTENDED_ENTITY_TYPES.items()},
        "entity_descriptions": {k: v["description"] for k, v in EXTENDED_ENTITY_TYPES.items()},
        "ngsi_version": "v2",
        "data_format": "application/json",
        "coordinate_reference": "WGS84",
        "smart_city_domains": [
            "Energy", "Transportation", "Environment", "Healthcare", "Public Safety",
            "Waste Management", "Water Management", "Public Services", "Retail",
            "Agriculture", "Tourism", "Infrastructure", "Entertainment"
        ],
        "description": "Comprehensive simulated IoT sensor data for FIWARE Smart City platform testing",
        "simulation_scale": "City-wide deployment with 30+ entity types"
    }
    
    with open('fiware_iot_data/comprehensive_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    generate_all_extended_data()
    create_comprehensive_metadata()
    print("Comprehensive FIWARE IoT data generation completed successfully!")