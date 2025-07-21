import requests
import json
import os


ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")
HEADERS = {
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH
}


def get_entities_by_type(entity_type):
    """
    Retrieves entities of a specific type from Orion Context Broker.
    """
    url = f"{ORION_URL}/v2/entities"
    params = {"type": entity_type}
    response = requests.get(url, headers=HEADERS, params=params)
    
    # --- ADDED PRINT STATEMENT FOR THE URL ---
    print(f"Querying Orion URL: {response.url}")
    # --- END ADDED PRINT STATEMENT ---

    if response.status_code == 200:
        entities = response.json()
        print(f"Successfully retrieved {len(entities)} entities of type '{entity_type}'.")
        return entities
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []

def extract_all_entity_info_to_dict(entity):
    """
    Extracts all available information from a single entity dictionary
    and returns it as a new dictionary.
    Handles nested 'value' fields commonly found in NGSI-v2 responses.
    """
    extracted_info = {
        "id": entity.get("id"),
        "type": entity.get("type")
    }
    print(f"WARNING : {extracted_info}")
    for key, attribute_data in entity.items():
        # Skip 'id' and 'type' as they are already added to the extracted_info dict
        if key in ['id', 'type']:
            continue

        if isinstance(attribute_data, dict):
            # Check if it's an attribute with 'value' (common in NGSI-v2)
            if 'value' in attribute_data:
                value = attribute_data['value']
                # Handle specific nested structures like geo:json coordinates
                if isinstance(value, dict) and value.get('type') == 'Point' and 'coordinates' in value:
                    extracted_info[key] = {
                        "lon": value['coordinates'][0],
                        "lat": value['coordinates'][1]
                    }
                else:
                    # For other nested dictionaries within 'value' or simple values
                    extracted_info[key] = value
            else:
                # If it's a dictionary but doesn't have 'value' key, store the whole dict
                extracted_info[key] = attribute_data
        else:
            # If it's a simple key-value pair directly in the entity
            extracted_info[key] = attribute_data
            
    return extracted_info

# Example of how to use the functions:
if __name__ == "__main__":
    # You can change this to any entity type you have in your Orion Context Broker
    entity_type_to_query = "OffStreetParking"

    entities_raw_data = get_entities_by_type(entity_type_to_query)
    #print(f"WARNING RAW DATA OF ORION: {entities_raw_data}") # This line seems to print raw data, consider removing for cleaner output if not needed for debugging
    if entities_raw_data:
        all_extracted_data = []
        for entity in entities_raw_data:
            extracted_entity_data = extract_all_entity_info_to_dict(entity)
            all_extracted_data.append(extracted_entity_data)

        print(json.dumps(all_extracted_data, indent=2))
        
    else:
        print(f"No entities of type '{entity_type_to_query}' found or an error occurred.")
