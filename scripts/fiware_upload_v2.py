import requests
import json
import os
import sys
import time
from typing import List, Optional

# --- Configuration ---
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")

# --- Helper Function ---
def make_request(method: str, url: str, headers: dict, json_data: dict, description: str = ""):
    """Send a request to Orion and print debug info."""
    print(f"\n--- {description} ---")
    print(f"POST {url}")
    print(f"Headers: {headers}")
    print(f"Entity: {json.dumps(json_data, indent=2)}")

    try:
        response = requests.request(method, url, headers=headers, json=json_data)
        response.raise_for_status()
        print(f"Success: {response.status_code}")
        if response.text:
            try:
                print("Response:", json.dumps(response.json(), indent=2))
            except Exception:
                print("Response:", response.text)
        return True
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh} -> {response.text}", file=sys.stderr)
    except requests.exceptions.ConnectionError as errc:
        print(f"Connection Error: {errc}", file=sys.stderr)
    except requests.exceptions.Timeout as errt:
        print(f"Timeout: {errt}", file=sys.stderr)
    except requests.exceptions.RequestException as err:
        print(f"Request Failed: {err}", file=sys.stderr)
    return False

# --- Load Entities ---
def load_entities(file_path: str) -> Optional[List[dict]]:
    """Load JSON entities from a file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [data]  # single entity
        return data  # list of entities
    except FileNotFoundError:
        print(f"File not found: {file_path}", file=sys.stderr)
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}", file=sys.stderr)
    return None

# --- Main Function ---
def push_entities_to_orion(entity_files: List[str]):
    headers = {
        "Content-Type": "application/json",
        "Fiware-Service": FIWARE_SERVICE,
        "Fiware-ServicePath": FIWARE_SERVICE_PATH
    }
    entities_url = f"{ORION_URL}/v2/entities"

    all_entities = []
    for file in entity_files:
        entities = load_entities(file)
        if entities:
            print(f"Loaded {len(entities)} entities from {file}")
            all_entities.extend(entities)

    if not all_entities:
        print("No entities loaded. Exiting.")
        return

    print("\n--- Pushing Entities to Orion ---")
    for entity in all_entities:
        make_request("POST", entities_url, headers=headers, json_data=entity,
                     description=f"Pushing {entity.get('id', 'N/A')}")
        time.sleep(0.1)  # avoid flooding Orion

    print("\nData population complete.")

# --- Entry Point ---
if __name__ == "__main__":
    print("FIWARE Generic Data Loader")

    # Ask user for file names instead of command-line arguments
    file_input = input("Enter the JSON file names (separated by spaces): ").strip()
    if not file_input:
        print("No files provided. Exiting.", file=sys.stderr)
        sys.exit(1)

    files = file_input.split()
    push_entities_to_orion(files)