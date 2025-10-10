import json
import csv
import requests
import os

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")

def upload_to_fiware(data, entity_type, context_broker_url):
    """
    Uploads a single entity or a list of entities to FIWARE Orion-LD.

    Args:
        data (dict or list): The entity data (or list of entities) to upload.
        entity_type (str): The type of the entity (e.g., "ParkingFacility", "Product", "Person").
        context_broker_url (str): The URL of the FIWARE Orion Context Broker's entities endpoint.
    """
    headers = {
        "Content-Type": "application/json", # For NGSI-v2, it's typically application/json
        "Accept": "application/json"
    }
    # For NGSI-v2, context is usually not in the Link header for entity creation unless specific attributes require it.
    # We will assume simple NGSI-v2 for now.

    if isinstance(data, list):
        for item in data:
            # Ensure each item has an 'id' and 'type' for NGSI-v2
            if "id" not in item:
                item["id"] = f"{entity_type}-{os.urandom(8).hex()}" # NGSI-v2 IDs are simpler
            if "type" not in item:
                item["type"] = entity_type

            # Convert NGSI-LD like attributes to NGSI-v2 format
            ngsiv2_item = {"id": item["id"], "type": item["type"]}
            for key, value_dict in item.items():
                if key not in ["id", "type"]:
                    if isinstance(value_dict, dict) and "value" in value_dict:
                        ngsiv2_item[key] = {"value": value_dict["value"], "type": value_dict.get("type", "Text")}
                    else:
                        ngsiv2_item[key] = {"value": value_dict, "type": "Text"} # Assume text if not a dict with 'value'

            try:
                response = requests.post(context_broker_url, headers=headers, json=ngsiv2_item)
                response.raise_for_status()  # Raise an exception for HTTP errors
                print(f"Successfully uploaded {entity_type} entity with ID: {ngsiv2_item['id']}")
            except requests.exceptions.RequestException as e:
                print(f"Error uploading {entity_type} entity with ID {ngsiv2_item.get('id', 'N/A')}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response content: {e.response.text}")
    else:
        # For a single dictionary, ensure it has 'id' and 'type'
        if "id" not in data:
            data["id"] = f"{entity_type}-{os.urandom(8).hex()}"
        if "type" not in data:
            data["type"] = entity_type

        # Convert NGSI-LD like attributes to NGSI-v2 format
        ngsiv2_data = {"id": data["id"], "type": data["type"]}
        for key, value_dict in data.items():
            if key not in ["id", "type"]:
                if isinstance(value_dict, dict) and "value" in value_dict:
                    ngsiv2_data[key] = {"value": value_dict["value"], "type": value_dict.get("type", "Text")}
                else:
                    ngsiv2_data[key] = {"value": value_dict, "type": "Text"} # Assume text if not a dict with 'value'

        try:
            response = requests.post(context_broker_url, headers=headers, json=ngsiv2_data)
            response.raise_for_status()
            print(f"Successfully uploaded {entity_type} entity with ID: {ngsiv2_data['id']}")
        except requests.exceptions.RequestException as e:
            print(f"Error uploading {entity_type} entity with ID {ngsiv2_data.get('id', 'N/A')}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")

def convert_csv_to_ngsiv2(csv_data, entity_type):
    """
    Converts CSV data into a list of NGSI-v2 compliant dictionaries.
    Each row becomes an entity, and columns become attributes.
    """
    entities = []
    reader = csv.DictReader(csv_data.splitlines())
    for row in reader:
        # Create a unique ID for the entity. Prioritize 'id' or 'Index' columns,
        # otherwise generate a random hex string.
        row_id_value = row.get('id') or row.get('Index')
        if row_id_value:
            entity_id = f"{entity_type}-{row_id_value}"
        else:
            entity_id = f"{entity_type}-{os.urandom(8).hex()}"

        entity = {
            "id": entity_id,
            "type": entity_type
        }
        for key, value in row.items():
            # Skip keys already used for ID generation
            if key in ["Index", "id"]:
                continue

            # Sanitize key for NGSI-v2 attribute name (remove spaces, etc.)
            sanitized_key = "".join(filter(str.isalnum, key))

            # Basic type inference for NGSI-v2 attributes
            if value.isdigit():
                entity[sanitized_key] = {"value": int(value), "type": "Number"}
            elif value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                entity[sanitized_key] = {"value": float(value), "type": "Number"}
            elif value.lower() in ["true", "false"]:
                entity[sanitized_key] = {"value": value.lower() == "true", "type": "Boolean"}
            else:
                entity[sanitized_key] = {"value": value, "type": "Text"}
        entities.append(entity)
    return entities

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    FIWARE_CONTEXT_BROKER_BASE_URL = ORION_URL
    if not FIWARE_CONTEXT_BROKER_BASE_URL:
        print("ERROR: Could not extract FIWARE_CONTEXT_BROKER_BASE_URL from fiware_query_tool.py.")
        print("Please ensure ORION_URL is defined in that file or manually set FIWARE_CONTEXT_BROKER_BASE_URL.")
        print("Exiting without uploading data.")
        return

    # Construct the full entities endpoint URL for NGSI-v2
    FIWARE_CONTEXT_BROKER_URL = f"{FIWARE_CONTEXT_BROKER_BASE_URL}/v2/entities"

    print(f"Using FIWARE Context Broker URL: {FIWARE_CONTEXT_BROKER_URL}")

    # --- Process all JSON and CSV files in the script directory ---
    for filename in os.listdir(script_dir):
        file_path = os.path.join(script_dir, filename)

        if filename.endswith(".json"):
            print(f"\n--- Processing {filename} ---")
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                entity_type = None
                # For JSON, we prioritize 'type' field within the data for NGSI-v2
                if isinstance(data, list) and data and "type" in data[0]:
                    entity_type = data[0]["type"]
                elif isinstance(data, dict) and "type" in data:
                    entity_type = data["type"]
                else:
                    # Fallback: derive from filename (e.g., parking_data.json -> ParkingData)
                    # This might need manual adjustment if filename doesn't map directly to entity type
                    entity_type = os.path.splitext(filename)[0].replace("_", "").title()

                if entity_type:
                    upload_to_fiware(data, entity_type, FIWARE_CONTEXT_BROKER_URL)
                else:
                    print(f"Could not determine entity type for {filename}. Skipping.")

            except FileNotFoundError:
                print(f"{filename} not found. Skipping.")
            except json.JSONDecodeError as e:
                print(f"Error decoding {filename}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {filename}: {e}")

        elif filename.endswith(".csv"):
            print(f"\n--- Processing {filename} ---")
            try:
                with open(file_path, "r") as f:
                    csv_data = f.read()
                # Derive entity type from the filename (e.g., people-100.csv -> People, new_cars.csv -> NewCars)
                # This logic tries to be flexible by taking the first part of the filename
                entity_type = os.path.splitext(filename)[0].split('-')[0].replace("_", "").title()
                entities = convert_csv_to_ngsiv2(csv_data, entity_type)
                upload_to_fiware(entities, entity_type, FIWARE_CONTEXT_BROKER_URL)
            except FileNotFoundError:
                print(f"{filename} not found. Skipping.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    main()