import requests
import json
import os
import sys
import time
from typing import List, Optional
from pathlib import Path

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
    except Exception as e:
        print(f"Error loading file {file_path}: {e}", file=sys.stderr)
    return None

# --- Discover JSON Files ---
def discover_json_files(path: str, recursive: bool = True) -> List[str]:
    """
    Discover JSON files in a given path.
    If path is a file, return it if it's a JSON file.
    If path is a directory, return all JSON files within it.
    """
    path_obj = Path(path)
    json_files = []
    
    if path_obj.is_file():
        if path_obj.suffix.lower() == '.json':
            json_files.append(str(path_obj))
        else:
            print(f"Warning: {path} is not a JSON file", file=sys.stderr)
    elif path_obj.is_dir():
        if recursive:
            # Recursively find all JSON files
            json_files.extend([str(p) for p in path_obj.rglob('*.json')])
        else:
            # Only find JSON files in the immediate directory
            json_files.extend([str(p) for p in path_obj.glob('*.json')])
        
        if not json_files:
            print(f"Warning: No JSON files found in directory {path}", file=sys.stderr)
        else:
            print(f"Found {len(json_files)} JSON files in {path}")
    else:
        print(f"Error: Path {path} does not exist", file=sys.stderr)
    
    return json_files

# --- Collect All Files ---
def collect_all_files(inputs: List[str], recursive: bool = True) -> List[str]:
    """
    Collect all JSON files from a list of file/folder paths.
    """
    all_files = []
    
    for input_path in inputs:
        files = discover_json_files(input_path.strip(), recursive)
        all_files.extend(files)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for file in all_files:
        if file not in seen:
            seen.add(file)
            unique_files.append(file)
    
    return unique_files

# --- Main Function ---
def push_entities_to_orion(entity_files: List[str]):
    """Push entities from multiple files to Orion Context Broker."""
    headers = {
        "Content-Type": "application/json",
        "Fiware-Service": FIWARE_SERVICE,
        "Fiware-ServicePath": FIWARE_SERVICE_PATH
    }
    entities_url = f"{ORION_URL}/v2/entities"

    all_entities = []
    successful_files = 0
    
    print(f"\nProcessing {len(entity_files)} files...")
    
    for file in entity_files:
        print(f"\nLoading file: {file}")
        entities = load_entities(file)
        if entities:
            print(f"✓ Loaded {len(entities)} entities from {file}")
            all_entities.extend(entities)
            successful_files += 1
        else:
            print(f"✗ Failed to load entities from {file}")

    if not all_entities:
        print("\nNo entities loaded. Exiting.")
        return

    print(f"\n--- Summary ---")
    print(f"Successfully loaded files: {successful_files}/{len(entity_files)}")
    print(f"Total entities to upload: {len(all_entities)}")

    print(f"\n--- Pushing {len(all_entities)} Entities to Orion ---")
    successful_uploads = 0
    
    for i, entity in enumerate(all_entities, 1):
        entity_id = entity.get('id', f'Entity_{i}')
        print(f"\nUploading entity {i}/{len(all_entities)}: {entity_id}")
        
        if make_request("POST", entities_url, headers=headers, json_data=entity,
                       description=f"Pushing {entity_id}"):
            successful_uploads += 1
        
        time.sleep(0.1)  # avoid flooding Orion

    print(f"\n--- Upload Complete ---")
    print(f"Successfully uploaded: {successful_uploads}/{len(all_entities)} entities")
    if successful_uploads < len(all_entities):
        print(f"Failed uploads: {len(all_entities) - successful_uploads}")

# --- Entry Point ---
if __name__ == "__main__":
    print("FIWARE Generic Data Loader (Enhanced)")
    print("Supports individual JSON files and folders")
    
    # Ask user for input
    file_input = input("\nEnter JSON files and/or folders (separated by spaces): ").strip()
    if not file_input:
        print("No input provided. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Ask if user wants recursive folder scanning
    recursive_input = input("Scan folders recursively? (y/N): ").strip().lower()
    recursive = recursive_input in ['y', 'yes', '1', 'true']

    inputs = file_input.split()
    
    # Collect all JSON files from the inputs
    json_files = collect_all_files(inputs, recursive)
    
    if not json_files:
        print("No JSON files found. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    print(f"\nFound {len(json_files)} JSON files total:")
    for file in json_files:
        print(f"  - {file}")
    
    # Confirm before proceeding
    confirm = input(f"\nProceed to upload entities from {len(json_files)} files? (Y/n): ").strip().lower()
    if confirm in ['n', 'no', '0', 'false']:
        print("Upload cancelled.")
        sys.exit(0)
    
    push_entities_to_orion(json_files)