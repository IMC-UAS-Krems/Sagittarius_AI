import json
import random
import uuid
from datetime import datetime, timezone
from faker import Faker

# Initialize Faker to generate mock data
fake = Faker()

# --- Configuration ---
# Central point for the city (Berlin, based on your examples)
CITY_CENTER_LAT = 52.52
CITY_CENTER_LON = 13.40
# Radius in degrees to spread the sensors around the city center
LOCATION_RADIUS = 0.08

# --- Helper Functions ---

def create_location():
    """Generates a random geo:json location within a radius of the city center."""
    return {
        "type": "geo:json",
        "value": {
            "latitude": round(random.uniform(CITY_CENTER_LAT - LOCATION_RADIUS, CITY_CENTER_LAT + LOCATION_RADIUS), 5),
            "longitude": round(random.uniform(CITY_CENTER_LON - LOCATION_RADIUS, CITY_CENTER_LON + LOCATION_RADIUS), 5)
        }
    }

def create_attribute(attr_type, value):
    """Creates a standard NGSI attribute structure."""
    return {"type": attr_type, "value": value}

def save_entity_to_file(entity, entity_type, count):
    """Saves a single entity dictionary to a JSON file."""
    filename = f"./output/{entity_type}_{count}.json"
    with open(filename, 'w') as f:
        json.dump(entity, f, indent=4)

# --- Entity Generation Functions ---

def create_air_quality_reading():
    """Generates a simulated air quality sensor reading."""
    entity_id = f"urn:ngsi-ld:AirQualityObserved:{uuid.uuid4()}"
    return {
        "id": entity_id,
        "type": "AirQualityObserved",
        "address": create_attribute("Text", fake.address()),
        "location": create_location(),
        "co": create_attribute("Number", round(random.uniform(0.5, 10), 2)),
        "no2": create_attribute("Number", round(random.uniform(10, 80), 2)),
        "o3": create_attribute("Number", round(random.uniform(20, 150), 2)),
        "pm25": create_attribute("Number", round(random.uniform(5, 50), 2)),
        "unitCode": create_attribute("Text", "GP"), # micrograms per cubic meter
        "dateObserved": create_attribute("DateTime", datetime.now(timezone.utc).isoformat())
    }

def create_waste_container_reading():
    """Generates a simulated smart waste container reading."""
    fill_level = round(random.random(), 2)
    status = "almostFull" if fill_level > 0.9 else "ok"
    entity_id = f"urn:ngsi-ld:WasteContainer:{uuid.uuid4()}"
    return {
        "id": entity_id,
        "type": "WasteContainer",
        "location": create_location(),
        "fillLevel": create_attribute("Number", fill_level),
        "status": create_attribute("Text", status),
        "lastEmptied": create_attribute("DateTime", fake.past_datetime(start_date="-7d", tzinfo=timezone.utc).isoformat()),
        "dateModified": create_attribute("DateTime", datetime.now(timezone.utc).isoformat())
    }

def create_streetlight_reading():
    """Generates a simulated streetlight status."""
    is_on = random.choice([True, False])
    status = "ok" if random.random() > 0.05 else "lampError"
    entity_id = f"urn:ngsi-ld:Streetlight:{uuid.uuid4()}"
    return {
        "id": entity_id,
        "type": "Streetlight",
        "location": create_location(),
        "status": create_attribute("Text", status),
        "powerState": create_attribute("Text", "on" if is_on else "off"),
        "dimmingLevel": create_attribute("Number", round(random.random(), 1) if is_on else 0),
        "dateModified": create_attribute("DateTime", datetime.now(timezone.utc).isoformat())
    }

def create_traffic_flow_reading():
    """Generates a simulated traffic flow observation on a road segment."""
    intensity = random.randint(5, 500)
    avg_speed = random.randint(10, 90)
    entity_id = f"urn:ngsi-ld:TrafficFlowObserved:{uuid.uuid4()}"
    return {
        "id": entity_id,
        "type": "TrafficFlowObserved",
        "laneId": create_attribute("Number", random.randint(1, 4)),
        "address": create_attribute("Text", fake.address()),
        "location": create_location(),
        "averageVehicleSpeed": create_attribute("Number", avg_speed),
        "intensity": create_attribute("Number", intensity), # Vehicles per hour
        "dateObserved": create_attribute("DateTime", datetime.now(timezone.utc).isoformat())
    }

# --- Main Generation Logic ---

if __name__ == "__main__":
    import os
    # Create an output directory if it doesn't exist
    if not os.path.exists("output"):
        os.makedirs("output")

    # Define how many files of each type you want to generate
    # Feel free to change these numbers to thousands!
    num_to_generate = {
        "AirQualityObserved": 100,
        "WasteContainer": 150,
        "Streetlight": 300,
        "TrafficFlowObserved": 200
    }

    print("Starting data generation...")

    for entity_type, count in num_to_generate.items():
        print(f"Generating {count} files for type: {entity_type}")
        for i in range(count):
            if entity_type == "AirQualityObserved":
                entity = create_air_quality_reading()
            elif entity_type == "WasteContainer":
                entity = create_waste_container_reading()
            elif entity_type == "Streetlight":
                entity = create_streetlight_reading()
            elif entity_type == "TrafficFlowObserved":
                entity = create_traffic_flow_reading()
            
            save_entity_to_file(entity, entity_type, i)

    print("\nData generation complete.")
    print(f"Files have been saved in the '{os.getcwd()}/output' directory.")