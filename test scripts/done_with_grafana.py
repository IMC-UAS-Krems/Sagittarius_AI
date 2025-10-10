import requests
import json
import time

# --- Configuration ---
# These URLs are based on the service names and exposed ports in your docker-compose.yaml
ORION_URL = "http://localhost:1026"
GRAFANA_URL = "http://localhost:3000"
GRAFANA_ADMIN_USER = "admin"
GRAFANA_ADMIN_PASSWORD = "admin" # Change this for production!

# --- Orion Context Broker Interaction ---

def create_or_update_entity(entity_data):
    """
    Creates or updates an entity in Orion Context Broker.
    Uses POST for creation and PATCH for updates if the entity already exists.
    """
    entity_id = entity_data.get('id')
    entity_type = entity_data.get('type')
    headers = {'Content-Type': 'application/ld+json'}

    try:
        # Check if entity exists
        response = requests.get(f"{ORION_URL}/entities/{entity_id}", headers=headers)
        if response.status_code == 200:
            print(f"Entity '{entity_id}' already exists. Updating...")
            # For updates, only send the attributes that need to be changed
            update_payload = {k: v for k, v in entity_data.items() if k not in ['id', 'type', '@context']}
            response = requests.patch(f"{ORION_URL}/entities/{entity_id}/attrs", headers=headers, data=json.dumps(update_payload))
        elif response.status_code == 404:
            print(f"Entity '{entity_id}' not found. Creating...")
            response = requests.post(f"{ORION_URL}/entities", headers=headers, data=json.dumps(entity_data))
        else:
            response.raise_for_status() # Raise an exception for other HTTP errors

        response.raise_for_status() # Raise an exception for HTTP errors (e.g., 4xx or 5xx)
        print(f"Successfully created/updated entity '{entity_id}'. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error interacting with Orion: {e}")
        if response is not None:
            print(f"Orion response: {response.status_code} - {response.text}")
        return False

def get_all_entities():
    """
    Retrieves all entities from Orion Context Broker.
    """
    headers = {'Content-Type': 'application/ld+json'}
    try:
        response = requests.get(f"{ORION_URL}/entities", headers=headers)
        response.raise_for_status()
        entities = response.json()
        print(f"Found {len(entities)} entities in Orion.")
        return entities
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving entities from Orion: {e}")
        return []

# --- Grafana Interaction ---

def grafana_api_call(method, endpoint, data=None):
    """
    Helper function to make authenticated API calls to Grafana.
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    auth = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)
    url = f"{GRAFANA_URL}/api/{endpoint}"

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, auth=auth)
        elif method == 'POST':
            response = requests.post(url, headers=headers, auth=auth, data=json.dumps(data))
        elif method == 'PUT':
            response = requests.put(url, headers=headers, auth=auth, data=json.dumps(data))
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, auth=auth)
        else:
            raise ValueError("Unsupported HTTP method")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making Grafana API call to {endpoint}: {e}")
        if response is not None:
            print(f"Grafana response: {response.status_code} - {response.text}")
        return None

def create_or_update_grafana_datasource(name="Fiware Orion (Infinity)", ds_type="yesoreyeram-infinity-datasource", url=ORION_URL):
    """
    Creates or updates the Grafana data source for Orion using the Infinity plugin.
    """
    # Check if data source already exists
    datasources = grafana_api_call('GET', 'datasources')
    if datasources:
        for ds in datasources:
            if ds.get('name') == name:
                print(f"Data source '{name}' already exists (ID: {ds['id']}). Updating...")
                # Update existing data source
                datasource_payload = {
                    "id": ds['id'],
                    "name": name,
                    "type": ds_type,
                    "url": url,
                    "access": "proxy", # Important for server-side requests
                    "isDefault": False,
                    "jsonData": {} # Infinity specific JSON data
                }
                response = grafana_api_call('PUT', f'datasources/{ds["id"]}', datasource_payload)
                if response:
                    print(f"Data source '{name}' updated successfully.")
                return response
    
    # Create new data source
    print(f"Data source '{name}' not found. Creating...")
    datasource_payload = {
        "name": name,
        "type": ds_type,
        "url": url,
        "access": "proxy",
        "isDefault": False,
        "jsonData": {}
    }
    response = grafana_api_call('POST', 'datasources', datasource_payload)
    if response:
        print(f"Data source '{name}' created successfully (ID: {response.get('id')}).")
    return response

def generate_dynamic_dashboard_json(entities, datasource_name="Fiware Orion (Infinity)"):
    """
    Generates a Grafana dashboard JSON dynamically based on entities and their attributes.
    This dashboard will display the *current* values of numerical attributes.
    """
    panels = []
    y_pos = 0 # For panel positioning

    # Get the data source ID
    datasources = grafana_api_call('GET', 'datasources')
    datasource_uid = None
    if datasources:
        for ds in datasources:
            if ds.get('name') == datasource_name:
                datasource_uid = ds.get('uid')
                break
    
    if not datasource_uid:
        print(f"Error: Data source '{datasource_name}' not found. Cannot generate dashboard.")
        return None

    panel_id_counter = 1

    for entity in entities:
        entity_id = entity.get('id')
        entity_type = entity.get('type')
        
        # Iterate through attributes to find numerical ones for display
        for attr_name, attr_value in entity.items():
            if attr_name not in ['id', 'type', '@context'] and isinstance(attr_value, dict) and 'value' in attr_value:
                value = attr_value['value']
                # Check if the value is numerical
                if isinstance(value, (int, float)):
                    # Create a Stat panel for each numerical attribute
                    panel_title = f"{entity_type}: {attr_name} ({entity_id})"
                    
                    # Infinity Data Source query for current value
                    # This assumes the Infinity data source is configured to proxy to Orion
                    # The URL path is /ngsi-ld/v1/entities/{entity_id}
                    # The data path is based on the JSON structure returned by Orion
                    infinity_query_target = {
                        "type": "json",
                        "source": "url",
                        "url": f"{ORION_URL}/entities/{entity_id}",
                        "root_is_content": True,
                        "data_path": f"$.{attr_name}.value", # Path to the actual value
                        "columns": [
                            {"selector": f"$.{attr_name}.value", "text": attr_name, "type": "number"}
                        ]
                    }

                    stat_panel = {
                        "id": panel_id_counter,
                        "gridPos": {"x": 0, "y": y_pos, "w": 12, "h": 4},
                        "type": "stat",
                        "title": panel_title,
                        "datasource": {"type": "datasource", "uid": datasource_uid},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "mappings": [],
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "red", "value": 80} # Example threshold
                                    ]
                                },
                                "unit": "none"
                            },
                            "overrides": []
                        },
                        "options": {
                            "colorMode": "value",
                            "graphMode": "none",
                            "justifyMode": "auto",
                            "orientation": "horizontal",
                            "reduceOptions": {
                                "calcs": ["lastNotNull"],
                                "fields": "",
                                "limit": 0,
                                "orderBy": "Last",
                                "reduce": True,
                                "values": False
                            },
                            "textMode": "auto"
                        },
                        "targets": [
                            {
                                "refId": "A",
                                "type": "json",
                                "source": "url",
                                "url": f"/ngsi-ld/v1/entities/{entity_id}", # Use relative path since DS URL is ORION_URL
                                "root_is_content": True,
                                "data_path": f"$.{attr_name}.value",
                                "columns": [
                                    {"selector": f"$.{attr_name}.value", "text": attr_name, "type": "number", "role": "value"}
                                ]
                            }
                        ]
                    }
                    panels.append(stat_panel)
                    y_pos += 4 # Move next panel down
                    panel_id_counter += 1

    dashboard_json = {
        "dashboard": {
            "id": None,
            "uid": None,
            "title": "Dynamic Fiware Context Dashboard",
            "tags": ["fiware", "dynamic", "context"],
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 0,
            "panels": panels,
            "refresh": "5s", # Refresh every 5 seconds to get latest context
            "time": {"from": "now-5m", "to": "now"},
            "timepicker": {},
            "templating": {"list": []},
            "annotations": {"list": []},
            "links": [],
            "gnetId": None,
            "description": "Automatically generated dashboard for Fiware context data (current state).",
            "editable": True,
            "graphTooltip": 1,
            "style": "dark",
            "nav": [
                {
                    "collapse": False,
                    "enable": True,
                    "hideFromMenu": False,
                    "icon": "dashboard",
                    "name": "General",
                    "type": "dashboards",
                    "url": ""
                }
            ]
        },
        "folderId": 0, # Or specify a folder ID if you have one
        "overwrite": True # Overwrite if a dashboard with the same title exists
    }
    return dashboard_json

def create_or_update_grafana_dashboard(dashboard_json):
    """
    Creates or updates a dashboard in Grafana.
    """
    if not dashboard_json:
        print("No dashboard JSON provided. Aborting dashboard creation.")
        return False

    title = dashboard_json['dashboard']['title']
    print(f"Attempting to create/update dashboard: '{title}'...")

    # Check if a dashboard with this title already exists
    search_results = grafana_api_call('GET', f'search?query={title}')
    existing_uid = None
    if search_results:
        for dash in search_results:
            if dash.get('title') == title:
                existing_uid = dash.get('uid')
                dashboard_json['dashboard']['uid'] = existing_uid # Set UID for update
                dashboard_json['dashboard']['id'] = dash.get('id') # Set ID for update
                break

    if existing_uid:
        print(f"Dashboard '{title}' found (UID: {existing_uid}). Updating...")
    else:
        print(f"Dashboard '{title}' not found. Creating...")

    response = grafana_api_call('POST', 'dashboards/db', dashboard_json)
    if response and response.get('status') == 'success':
        print(f"Dashboard '{title}' successfully created/updated. URL: {GRAFANA_URL}{response.get('url')}")
        return True
    else:
        print(f"Failed to create/update dashboard '{title}'.")
        return False

# --- Main Script Execution ---

if __name__ == "__main__":
    print("--- Starting Fiware-Grafana Interaction Script ---")

    # 1. Create/Update Sample Entities in Orion
    print("\n--- Creating/Updating Sample Entities in Orion ---")
    
    # Example 1: Smart Device
    device_entity = {
        "id": "urn:ngsi-ld:Device:sensor001",
        "type": "Device",
        "temperature": {
            "type": "Property",
            "value": 25.5,
            "unitCode": "CEL",
            "observedAt": "2025-07-15T10:00:00Z"
        },
        "humidity": {
            "type": "Property",
            "value": 60,
            "unitCode": "P1",
            "observedAt": "2025-07-15T10:00:00Z"
        },
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [ -3.703790, 40.416775 ]
            }
        },
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-contexts/ngsi-ld-default.jsonld",
            "https://schema.org/docs/jsonldcontext.json" # Example additional context
        ]
    }
    create_or_update_entity(device_entity)

    # Example 2: Room Occupancy Sensor
    room_sensor_entity = {
        "id": "urn:ngsi-ld:Sensor:roomA-occupancy",
        "type": "Sensor",
        "occupancy": {
            "type": "Property",
            "value": 3,
            "unitCode": "C62", # Persons
            "observedAt": "2025-07-15T10:05:00Z"
        },
        "lightLevel": {
            "type": "Property",
            "value": 750,
            "unitCode": "LUX",
            "observedAt": "2025-07-15T10:05:00Z"
        },
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-contexts/ngsi-ld-default.jsonld"
        ]
    }
    create_or_update_entity(room_sensor_entity)

    # Example 3: Weather Station (update existing to demonstrate)
    weather_station_entity = {
        "id": "urn:ngsi-ld:WeatherStation:station001",
        "type": "WeatherStation",
        "temperature": {
            "type": "Property",
            "value": 28.1,
            "unitCode": "CEL",
            "observedAt": "2025-07-15T10:10:00Z"
        },
        "pressure": {
            "type": "Property",
            "value": 1012.5,
            "unitCode": "BAR", # HectoPascals
            "observedAt": "2025-07-15T10:10:00Z"
        },
        "windSpeed": {
            "type": "Property",
            "value": 15.2,
            "unitCode": "KMH",
            "observedAt": "2025-07-15T10:10:00Z"
        },
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-contexts/ngsi-ld-default.jsonld"
        ]
    }
    create_or_update_entity(weather_station_entity)

    # Give Orion a moment to process (optional, but good practice)
    time.sleep(2)

    # 2. Configure Grafana Data Source
    print("\n--- Configuring Grafana Data Source ---")
    datasource_created = create_or_update_grafana_datasource()
    if not datasource_created:
        print("Failed to create/update Grafana data source. Please check Grafana logs and credentials.")
        exit()
    
    # Give Grafana a moment to register the data source
    time.sleep(2)

    # 3. Retrieve Entities from Orion to Infer Data Structure
    print("\n--- Retrieving Entities from Orion ---")
    all_entities = get_all_entities()

    if not all_entities:
        print("No entities found in Orion. Cannot generate dashboard.")
        exit()

    # 4. Generate and Upload Dynamic Grafana Dashboard
    print("\n--- Generating and Uploading Dynamic Grafana Dashboard ---")
    dynamic_dashboard_json = generate_dynamic_dashboard_json(all_entities)

    if dynamic_dashboard_json:
        create_or_update_grafana_dashboard(dynamic_dashboard_json)
    else:
        print("Failed to generate dashboard JSON.")

    print("\n--- Script Finished ---")
    print("You can now access Grafana at http://localhost:3000 and view the 'Dynamic Fiware Context Dashboard'.")
    print("Remember: This dashboard shows CURRENT context data. For historical data, integrate QuantumLeap or CrateDB.")
