import requests
import json
import os
import sys
from typing import List, Dict, Any, Optional

# --- Configuration ---
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")

# --- Helper for Orion Queries ---
def _make_orion_query(params: Dict[str, Any], description: str) -> Optional[List[Dict]]:
    """Helper to make GET requests to Orion Context Broker."""
    url = f"{ORION_URL}/v2/entities"
    headers = {
        "Fiware-Service": FIWARE_SERVICE,
        "Fiware-ServicePath": FIWARE_SERVICE_PATH,
        "Accept": "application/json"
    }
    print(f"\n--- Querying Orion: {description} ---")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Response Status: {response.status_code}")
        try:
            json_response = response.json()
            # print(f"Response Body: {json.dumps(json_response, indent=2)}") # Uncomment for full response
            return json_response
        except json.JSONDecodeError:
            print(f"Response Body (text): {response.text}")
            return None
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error querying Orion: {errh}", file=sys.stderr)
        if response is not None:
            print(f"Response Text: {response.text}", file=sys.stderr)
        return None
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting to Orion: {errc}. Is Orion running at {ORION_URL}?", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Orion query: {e}", file=sys.stderr)
        return None

# --- Interaction Functions ---
def get_closest_parking_lot_info(user_latitude: float, user_longitude: float, max_distance_meters: Optional[float] = 1000.0) -> str:
    """
    Finds the closest parking lot with available spaces near a given latitude and longitude.
    """
    try:
        params = {
            "type": "OffStreetParking", # Specify type for parking entities
            "georel": f"near;maxDistance:{max_distance_meters}",
            "geometry": "point",
            "coords": f"{user_latitude},{user_longitude}",
            "options": "keyValues" # Get simplified key-value pairs
        }
        parking_lots = _make_orion_query(params, "Finding closest parking lot")

        if not parking_lots:
            return "No parking lots found within the specified distance or an error occurred during query."

        # Filter for parking lots with available spaces
        available_parking_lots = [
            pl for pl in parking_lots
            if pl.get('availableSpotNumber', 0) > 0
        ]

        if not available_parking_lots:
            return "No parking lots with available spaces found within the specified distance."

        # Sort by distance (Orion's 'near' typically sorts by distance, but explicit sort can be added if needed)
        closest_lot = available_parking_lots[0]

        name = closest_lot.get('name', closest_lot.get('id', 'Unknown Parking Lot'))
        address = closest_lot.get('address', 'N/A')
        available_spots = closest_lot.get('availableSpotNumber', 'N/A')
        total_spots = closest_lot.get('totalSpotNumber', 'N/A')
        location_coords = closest_lot.get('location', {}).get('coordinates', 'N/A')

        response_str = (
            f"The closest parking lot with available spaces is '{name}'.\n"
            f"Address: {address}\n"
            f"Available Spots: {available_spots} / Total Spots: {total_spots}\n"
            f"Coordinates: {location_coords}"
        )
        return response_str
    except Exception as e:
        return f"An error occurred while finding the closest parking lot: {e}"

def get_product_details(product_name: str) -> str:
    """
    Retrieves information about a product, including its price, location, and sale status.
    """
    try:
        params = {
            "type": "Product",
            "q": f"name~={product_name}", # Case-insensitive partial match for name
            "options": "keyValues"
        }
        products = _make_orion_query(params, f"Searching for product: {product_name}")

        if not products:
            return f"No product found matching '{product_name}' or an error occurred during query."

        response_lines = [f"Here's what I found for '{product_name}':"]
        for product in products:
            product_id = product.get('id', 'N/A')
            name = product.get('name', 'N/A')
            price = product.get('price', 'N/A')
            currency = product.get('currency', 'EUR') # Assuming EUR as default
            on_sale = product.get('onSale', False)
            sale_price = product.get('salePrice', 'N/A')
            shop_id = product.get('shop', 'N/A')

            sale_status = ""
            if on_sale and sale_price != 'N/A':
                sale_status = f" (ON SALE! Sale Price: {sale_price} {currency})"
            elif on_sale:
                sale_status = " (ON SALE!)"

            response_lines.append(f"- Product: {name} (ID: {product_id})")
            response_lines.append(f"  Price: {price} {currency}{sale_status}")
            if shop_id != 'N/A':
                response_lines.append(f"  Available at Shop ID: {shop_id}")
            response_lines.append("") # Empty line for separation

        return "\n".join(response_lines).strip()
    except Exception as e:
        return f"An error occurred while retrieving product information: {e}"

if __name__ == "__main__":
    print("Starting Fiware Data Interaction Script...")

    # --- Test Cases ---

    # Test 1: Find closest parking lot
    user_lat = 52.5200 # Berlin city center example
    user_lon = 13.4050
    print("\n--- Test Case: Finding closest parking lot with available spaces ---")
    parking_result = get_closest_parking_lot_info(user_lat, user_lon, max_distance_meters=2000)
    print(parking_result)

    # Test 2: Find a specific product
    print("\n--- Test Case: Getting info for 'Laptop XYZ' ---")
    laptop_result = get_product_details("Laptop XYZ")
    print(laptop_result)

    # Test 3: Find a product on sale
    print("\n--- Test Case: Getting info for 'Cool T-Shirt' ---")
    tshirt_result = get_product_details("Cool T-Shirt")
    print(tshirt_result)

    # Test 4: Find a product that doesn't exist
    print("\n--- Test Case: Getting info for 'NonExistentItem' ---")
    non_existent_result = get_product_details("NonExistentItem")
    print(non_existent_result)

    print("\nFiware Data Interaction Script Finished.")