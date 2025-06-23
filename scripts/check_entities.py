import requests
import os
import json

# Configuration (use the same as your populate script)
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")

HEADERS = {
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH
}

def get_all_entities():
    url = f"{ORION_URL}/v2/entities"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        entities = response.json()
        print(f"\nRetrieved {len(entities)} entities:")
        print(json.dumps(entities, indent=2))
    else:
        print(f"Error {response.status_code}: {response.text}")

def get_entities_by_type(entity_type):
    url = f"{ORION_URL}/v2/entities"
    params = {"type": entity_type}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        entities = response.json()
        print(f"\nRetrieved {len(entities)} entities of type '{entity_type}':")
        print(json.dumps(entities, indent=2))
    else:
        print(f"Error {response.status_code}: {response.text}")

def get_entity_by_id(entity_id):
    url = f"{ORION_URL}/v2/entities/{entity_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        print(f"\nEntity '{entity_id}' found:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    print("Options:")
    print("1. List all entities")
    print("2. List entities by type")
    print("3. Get entity by ID")
    choice = input("Choose an option (1/2/3): ").strip()

    if choice == "1":
        get_all_entities()
    elif choice == "2":
        entity_type = input("Enter entity type (e.g., OffStreetParking or Product): ").strip()
        get_entities_by_type(entity_type)
    elif choice == "3":
        entity_id = input("Enter full entity ID (e.g., urn:ngsi-ld:Product:LaptopXYZ_ShopA): ").strip()
        get_entity_by_id(entity_id)
    else:
        print("Invalid choice.")
