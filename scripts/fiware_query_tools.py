import os
import requests
import json
import sys
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- Fiware Configuration (Environment Variables) ---
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service") # Ensure this matches your FIWARE_SERVICE in docker-compose
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data") # Ensure this matches your FIWARE_SERVICE_PATH

class GetClosestParkingLotInput(BaseModel):
    user_latitude: float = Field(description="The user's current latitude.")
    user_longitude: float = Field(description="The user's current longitude.")
    max_distance_meters: Optional[float] = Field(None, description="Optional maximum distance in meters to search for a parking lot. Defaults to 1000m (1km).")

class GetProductInfoInput(BaseModel):
    product_name: str = Field(description="The name of the product to search for (case-insensitive partial match).")

class FiwareQueryTools:
    """
    A collection of tools for querying data from the Fiware Orion Context Broker.
    """
    def __init__(self):
        self.headers = {
            "Fiware-Service": FIWARE_SERVICE,
            "Fiware-ServicePath": FIWARE_SERVICE_PATH,
            "Accept": "application/json"
        }

    def _make_orion_query(self, params: Dict[str, Any], description: str) -> Optional[List[Dict]]:
        """Helper to make GET requests to Orion Context Broker."""
        url = f"{ORION_URL}/v2/entities"
        print(f"\n--- Querying Orion: {description} ---")
        print(f"URL: {url}")
        print(f"Headers: {self.headers}")
        print(f"Params: {params}")

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            print(f"Response Status: {response.status_code}")
            try:
                json_response = response.json()
                print(f"Response Body: {json.dumps(json_response, indent=2)}")
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

    @tool(args_schema=GetClosestParkingLotInput)
    def get_closest_parking_lot(self, user_latitude: float, user_longitude: float, max_distance_meters: Optional[float] = 1000.0) -> str:
        """
        Finds the closest parking lot with available spaces near a given latitude and longitude.

        Args:
            user_latitude (float): The latitude of the user's current location.
            user_longitude (float): The longitude of the user's current location.
            max_distance_meters (float, optional): The maximum distance in meters to search for parking lots. Defaults to 1000m (1km).

        Returns:
            str: A descriptive string of the closest parking lot found with available spaces,
                 or a message indicating none were found or an error occurred.
        """
        try:
            params = {
                "type": "OffStreetParking,ParkingSite", # Common types for parking
                "georel": f"near;maxDistance:{max_distance_meters}",
                "geometry": "point",
                "coords": f"{user_latitude},{user_longitude}",
                "options": "keyValues" # Get simplified key-value pairs
            }
            parking_lots = self._make_orion_query(params, "Finding closest parking lot")

            if not parking_lots:
                return "No parking lots found within the specified distance or an error occurred during query."

            # Filter for parking lots with available spaces
            available_parking_lots = [
                pl for pl in parking_lots
                if pl.get('availableSpotNumber', 0) > 0 # Assumes 'availableSpotNumber' attribute
            ]

            if not available_parking_lots:
                return "No parking lots with available spaces found within the specified distance."

            # Sort by distance (Orion's 'near' typically sorts by distance, but explicit sort can be added if needed)
            # For simplicity, we'll assume the first one is the closest as per georel=near
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

    @tool(args_schema=GetProductInfoInput)
    def get_product_info(self, product_name: str) -> str:
        """
        Retrieves information about a product, including its price, location, and sale status.

        Args:
            product_name (str): The name of the product to search for (case-insensitive partial match).

        Returns:
            str: A descriptive string of the product information, including prices and sales,
                 or a message indicating the product was not found or an error occurred.
        """
        try:
            # Query for Product entities matching the name
            params = {
                "type": "Product",
                "q": f"name~={product_name}", # Case-insensitive partial match
                "options": "keyValues"
            }
            products = self._make_orion_query(params, f"Searching for product: {product_name}")

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
                shop_id = product.get('shop', 'N/A') # Assuming 'shop' attribute stores the ID of the shop entity

                sale_status = ""
                if on_sale and sale_price != 'N/A':
                    sale_status = f" (ON SALE! Sale Price: {sale_price} {currency})"
                elif on_sale:
                    sale_status = " (ON SALE!)"

                response_lines.append(f"- Product: {name} (ID: {product_id})")
                response_lines.append(f"  Price: {price} {currency}{sale_status}")
                if shop_id != 'N/A':
                    # Optionally, you could make another query here to get the shop's full name/address
                    # For simplicity, we'll just show the shop ID
                    response_lines.append(f"  Available at Shop ID: {shop_id}")
                response_lines.append("") # Empty line for separation

            return "\n".join(response_lines).strip()
        except Exception as e:
            return f"An error occurred while retrieving product information: {e}"