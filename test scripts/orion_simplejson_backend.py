from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# --- Configuration (must match your main script and Orion setup) ---
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")
HEADERS = {
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
    "Content-Type": "application/json"
}

# --- SimpleJSON API Endpoints ---

@app.route('/orion-data/', methods=['GET'])
def root():
    """Health check endpoint for the SimpleJSON API."""
    return "Orion SimpleJSON API is running!", 200

@app.route('/orion-data/search', methods=['POST'])
def search():
    """
    Grafana calls this endpoint to get a list of available metrics/targets.
    You can return a list of entity_id/attribute combinations that your API supports.
    For simplicity, this example returns a generic list. In a real app, you might
    query Orion for available entity types and their common attributes.
    """
    print("[API] /search request received.")
    # Example: Return some common attributes you expect to visualize
    return jsonify([
        {"text": "Available Spot Number", "value": "availableSpotNumber"},
        {"text": "Total Spot Number", "value": "totalSpotNumber"},
        {"text": "Temperature", "value": "temperature"}, # Example for other entity types
        {"text": "Humidity", "value": "humidity"}
    ])

@app.route('/orion-data/query', methods=['POST'])
def query():
    """
    Grafana calls this endpoint to get actual data for panels.
    It receives a JSON payload with 'targets' (from dashboard panel configurations)
    and 'range' (time range).
    """
    req = request.json
    targets = req.get('targets', [])
    # range_from = req.get('range', {}).get('from') # For time series queries
    # range_to = req.get('range', {}).get('to')

    print(f"[API] /query request received. Targets: {targets}")

    results = []
    for target in targets:
        ref_id = target.get('refId')
        query_type = target.get('query_type') # Our custom query type
        entity_id = target.get('entity_id')
        attribute = target.get('attribute')

        if query_type == "current_value" and entity_id and attribute:
            # Fetch current value from Orion Context Broker
            orion_url = f"{ORION_URL}/v2/entities/{entity_id}?options=keyValues"
            try:
                orion_response = requests.get(orion_url, headers=HEADERS)
                orion_response.raise_for_status()
                entity_data = orion_response.json()

                value = entity_data.get(attribute)
                if value is not None:
                    # For gauge/stat panels, SimpleJSON expects a "table" format
                    # with a single row for the current value.
                    results.append({
                        "columns": [
                            {"text": "Time", "type": "time"},
                            {"text": attribute, "type": "number"}
                        ],
                        "rows": [
                            [int(time.time() * 1000), value] # Current timestamp in milliseconds
                        ],
                        "type": "table",
                        "refId": ref_id
                    })
                    print(f"[API] Fetched current value for {entity_id}.{attribute}: {value}")
                else:
                    print(f"[API] Attribute '{attribute}' not found for entity '{entity_id}'.")
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Error fetching from Orion in SimpleJSON API for {entity_id}.{attribute}: {e}")
                # You might want to return an empty result or an error indicator to Grafana
        # Add more query_type handlers here if you want to support time series, etc.
        # For time series, you'd typically query a historical component (like QuantumLeap or MongoDB)
        # and return data in the "timeseries" format: [{"target": "metric_name", "datapoints": [[value, timestamp], ...]}]

    return jsonify(results)

@app.route('/orion-data/annotations', methods=['POST'])
def annotations():
    """
    Grafana calls this for annotations. Can return an empty list if not used.
    """
    print("[API] /annotations request received.")
    return jsonify([])

if __name__ == '__main__':
    print(f"Starting Orion SimpleJSON API on http://localhost:5000/orion-data")
    print("Ensure Orion Context Broker is running and accessible.")
    app.run(debug=True, port=5000) # Run on port 5000, adjust if needed