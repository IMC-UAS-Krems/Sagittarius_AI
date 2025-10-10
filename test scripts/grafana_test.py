import requests
import json
import os

# --- Re-using functions from your original entity_attributes.py script ---

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
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        entities = response.json()
        print(f"Successfully retrieved {len(entities)} entities of type '{entity_type}'.")
        return entities
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving entities from Orion: {e}")
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

# --- New function to generate Grafana Dashboard JSON ---

def generate_grafana_dashboard(entities_data, entity_type_to_query, dashboard_title="FIWARE Entity Attributes Dashboard"):
    """
    Generates a Grafana dashboard JSON structure from extracted entity data.
    The dashboard will contain a single table panel displaying all entity attributes,
    configured to use the Infinity Data Source to query Orion Context Broker.

    Args:
        entities_data (list): A list of dictionaries, where each dictionary
                              represents an entity with its extracted attributes.
        entity_type_to_query (str): The type of entity being queried (e.g., "Product").
                                    Used to construct the Orion API URL.
        dashboard_title (str): The title for the Grafana dashboard.

    Returns:
        dict: A Python dictionary representing the Grafana dashboard JSON.
    """

    # Initialize a basic Grafana dashboard structure
    dashboard = {
        "annotations": {"list": []},
        "description": "Automatically generated dashboard for FIWARE Orion Context Broker entity attributes using Infinity Data Source.",
        "editable": True,
        "gnetId": None,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "panels": [],
        "schemaVersion": 30, # Use a recent schema version for Grafana 8+
        "style": "dark",
        "tags": ["fiware", "orion", "auto-generated", "infinity"],
        "templating": {"list": []},
        "time": {"from": "now-5m", "to": "now"}, # Default time range
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"],
            "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"]
        },
        "timezone": "browser",
        "title": dashboard_title,
        "uid": None, # Grafana will assign a UID on import
        "version": 1,
        "weekStart": ""
    }

    # Determine all unique column names from the entities_data
    all_keys = set()
    for entity in entities_data:
        all_keys.update(entity.keys())
    
    # Sort keys for consistent column order
    sorted_keys = sorted(list(all_keys))

    # Create columns configuration for the Infinity Data Source
    infinity_columns = []
    for key in sorted_keys:
        # For simplicity, all extracted attributes are treated as strings.
        # If specific types (number, boolean) are needed, this logic would be more complex.
        infinity_columns.append({"selector": key, "text": key, "type": "string"})

    # Add a Table panel to display all extracted attributes
    table_panel = {
        "datasource": {
            "type": "infinity",
            # IMPORTANT: Replace "your_infinity_datasource_uid_here" with the actual UID
            # of your configured Infinity Data Source in Grafana.
            "uid": "your_infinity_datasource_uid_here" 
        },
        "fieldConfig": {
            "defaults": {
                "custom": {},
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}]
                }
            },
            "overrides": []
        },
        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 0}, # Full width row
        "id": 1, # Unique panel ID
        "options": {
            "showHeader": True,
            "sortBy": [],
            "frameIndex": 0,
            "rowHeight": "auto",
            "cellHeight": "sm",
            "footer": {
                "countRows": False,
                "reducer": 0,
                "show": False,
                "fields": ""
            }
        },
        "pluginVersion": "8.x.x", # Adjust based on your Grafana version
        "targets": [
            {
                "refId": "A",
                "type": "json", # This specifies the Infinity query type for JSON data
                # URL to query Orion Context Broker for entities of the specified type
                "url": f"{ORION_URL}/v2/entities?type={entity_type_to_query}", 
                "method": "GET",
                "root_field": "", # Use empty string for array at the root of the JSON response
                "columns": infinity_columns, # Dynamically generated columns
                "format": "table",
                "data_options": { # Headers for Fiware-Service and Fiware-ServicePath
                    "headers": [
                        {"key": "Fiware-Service", "value": FIWARE_SERVICE},
                        {"key": "Fiware-ServicePath", "value": FIWARE_SERVICE_PATH}
                    ]
                }
            }
        ],
        "title": f"FIWARE {entity_type_to_query} Attributes",
        "type": "table"
    }

    dashboard["panels"].append(table_panel)

    return dashboard

# --- Example Usage ---
if __name__ == "__main__":
    # You can change this to any entity type you have in your Orion Context Broker
    entity_type_to_query = "Product" 

    # 1. Get raw entities from Orion
    entities_raw_data = get_entities_by_type(entity_type_to_query)

    if entities_raw_data:
        # 2. Extract all relevant information into a list of dictionaries
        all_extracted_data = []
        for entity in entities_raw_data:
            extracted_entity_data = extract_all_entity_info_to_dict(entity)
            all_extracted_data.append(extracted_entity_data)

        # Print the extracted data (for verification, similar to your original script)
        print("\n--- Extracted Entity Data ---")
        print(json.dumps(all_extracted_data, indent=2))

        # 3. Generate the Grafana dashboard JSON
        dashboard_json = generate_grafana_dashboard(
            all_extracted_data,
            entity_type_to_query, # Pass entity_type_to_query to the function
            f"FIWARE {entity_type_to_query} Attributes Dashboard"
        )

        # 4. Print the generated Grafana dashboard JSON
        print("\n--- Generated Grafana Dashboard JSON ---")
        print(json.dumps(dashboard_json, indent=2))

        # Optional: Save to a file
        output_filename = f"{entity_type_to_query.lower()}_dashboard.json"
        with open(output_filename, "w") as f:
            json.dump(dashboard_json, f, indent=2)
        print(f"\nGrafana dashboard saved to {output_filename}")

    else:
        print(f"No entities of type '{entity_type_to_query}' found or an error occurred. Cannot generate dashboard.")