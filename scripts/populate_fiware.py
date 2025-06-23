import requests
import json
import os
import time
import sys
from typing import Optional

# --- Configuration ---
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
# QUANTUMLEAP_URL is no longer needed as QuantumLeap is not used in this script

# Ensure these match your docker-compose.yml and fiware_query_tools.py
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")

# --- Helper Function for API Calls ---
def make_request(method, url, headers=None, data=None, json_data=None, params=None, description=""):
    """Helper to make HTTP requests and handle responses."""
    print(f"\n--- {description} ---")
    print(f"URL: {url}")
    if headers:
        print(f"Headers: {headers}")
    if data:
        print(f"Data: {data}")
    if json_data:
        print(f"JSON Data: {json.dumps(json_data, indent=2)}")
    if params:
        print(f"Params: {params}")

    try:
        response = requests.request(method, url, headers=headers, json=json_data, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Response Status: {response.status_code}")
        try:
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            print(f"Response Body (text): {response.text}")
        return response
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}", file=sys.stderr)
        if response is not None:
            print(f"Response Text: {response.text}", file=sys.stderr)
        return None
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}. Is the Fiware component running at {url}?", file=sys.stderr)
        return None
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred: {err}", file=sys.stderr)
        return None

# --- Main Population Logic ---
def populate_fiware_with_data(parking_data_path: Optional[str], product_data_path: Optional[str]):
    """
    Reads parking and product data from JSON files and pushes them to Fiware Orion.
    Allows for one or both file paths to be optional.
    This version does NOT interact with QuantumLeap.
    """
    orion_headers = {
        "Content-Type": "application/json",
        "Fiware-Service": FIWARE_SERVICE,
        "Fiware-ServicePath": FIWARE_SERVICE_PATH
    }
    orion_entities_url = f"{ORION_URL}/v2/entities"

    all_entities = []
    data_loaded = False

    # 1. Load Parking Data
    if parking_data_path:
        try:
            with open(parking_data_path, 'r') as f:
                parking_entities = json.load(f)
                all_entities.extend(parking_entities)
            print(f"Loaded {len(parking_entities)} parking entities from {parking_data_path}")
            data_loaded = True
        except FileNotFoundError:
            print(f"Warning: Parking data file not found at '{parking_data_path}'. Skipping parking data.", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in parking data file '{parking_data_path}'. Skipping parking data.", file=sys.stderr)

    # 2. Load Product Data
    if product_data_path:
        try:
            with open(product_data_path, 'r') as f:
                product_entities = json.load(f)
                all_entities.extend(product_entities)
            print(f"Loaded {len(product_entities)} product entities from {product_data_path}")
            data_loaded = True
        except FileNotFoundError:
            print(f"Warning: Product data file not found at '{product_data_path}'. Skipping product data.", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in product data file '{product_data_path}'. Skipping product data.", file=sys.stderr)

    if not data_loaded:
        print("No valid data files provided or loaded. Exiting population process.", file=sys.stderr)
        return

    # 3. QuantumLeap Subscription creation removed as it's not needed.
    print("\n--- Skipping QuantumLeap Subscription (not used in this script) ---")

    # 4. Push Entities to Orion
    print("\n--- Pushing Entities to Orion Context Broker ---")
    if not all_entities:
        print("No entities to push to Orion after loading files.", file=sys.stderr)
        return # Exit if no entities were loaded

    for entity in all_entities:
        # --- FIX APPLIED HERE: Removed `params={"options": "append,overwrite"}` ---
        # For POST /v2/entities, the create-or-update behavior is typically implicit.
        # If entity exists, it updates. If not, it creates.
        make_request("POST", orion_entities_url, headers=orion_headers, json_data=entity,
                     description=f"Pushing entity: {entity.get('id', 'N/A')} ({entity.get('type', 'N/A')})")
        time.sleep(0.1) # Small delay to avoid overwhelming Orion

    # 5. QuantumLeap wait time removed.
    print("\n--- Data Population Complete. Data is now in Orion Context Broker. ---")


if __name__ == "__main__":
    print("Starting Fiware Data Population Script...")
    print("NOTE: Ensure Orion Context Broker is running.")
    print("Ensure 'requests' is installed: pip install requests")

    script_dir = os.path.dirname(__file__)

    # Prompt user for parking data file path (optional)
    parking_input = input("Enter the path or filename for parking data (e.g., parking_data.txt or C:/data/parking.json). Leave blank to skip: ").strip()
    parking_data_file = None
    if parking_input:
        if not os.path.isabs(parking_input):
            parking_data_file = os.path.join(script_dir, parking_input)
        else:
            parking_data_file = parking_input
        if not os.path.exists(parking_data_file):
            print(f"Warning: Parking data file not found at '{parking_data_file}'. It will be skipped.", file=sys.stderr)
            parking_data_file = None # Ensure it's None if not found

    # Prompt user for product data file path (optional)
    product_input = input("Enter the path or filename for product data (e.g., product_data.txt or C:/data/products.json). Leave blank to skip: ").strip()
    product_data_file = None
    if product_input:
        if not os.path.isabs(product_input):
            product_data_file = os.path.join(script_dir, product_input)
        else:
            product_data_file = product_input
        if not os.path.exists(product_data_file):
            print(f"Warning: Product data file not found at '{product_data_file}'. It will be skipped.", file=sys.stderr)
            product_data_file = None # Ensure it's None if not found

    # Only proceed if at least one file path was successfully provided/found
    if not parking_data_file and not product_data_file:
        print("No valid parking or product data files were provided. The script will not populate Fiware.", file=sys.stderr)
        sys.exit(0) # Exit gracefully

    populate_fiware_with_data(parking_data_file, product_data_file)
    print("\nFiware Data Population Script Finished.")
