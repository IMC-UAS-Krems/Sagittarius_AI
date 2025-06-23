import requests
import os
from typing import List, Dict, Any, Optional
from langchain.tools import tool

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")

class FiwareQueryTools:

    def __init__(self):
        pass

    @staticmethod # Decorator to make it a static method
    def make_fiware_request(url: str, params: Optional[Dict] = None) -> Optional[List[Dict]]:
        headers = {
            "Fiware-Service": FIWARE_SERVICE,
            "Fiware-ServicePath": FIWARE_SERVICE_PATH,
            "Accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Fiware: {e}")
            return None

    @tool # Langchain tool decorator
    @staticmethod # Decorator to make it a static method
    def get_parking_spots(user_latitude: float, user_longitude: float) -> str:
        """
        Retrieves parking spot information from Fiware and finds the closest free spot.
        If no free spots, returns closest available alternatives.
        Requires user's current latitude and longitude.
        """
        url = f"{ORION_URL}/v2/entities"
        params = {
            "type": "ParkingSpot",
            "options": "keyValues"
        }
        # Call the static method using the class name
        parking_data = FiwareQueryTools.make_fiware_request(url, params)

        if not parking_data:
            return "Could not retrieve parking data from Fiware."

        free_spots = []
        all_spots = []

        for spot in parking_data:
            spot_info = {
                "id": spot.get("id"),
                "location": spot.get("location"), # Assuming location is { "latitude": X, "longitude": Y }
                "availableSpotNumber": spot.get("availableSpotNumber"),
                "totalSpotNumber": spot.get("totalSpotNumber"),
                "name": spot.get("name", "Unknown Parking Spot")
            }
            all_spots.append(spot_info)
            if spot_info.get("availableSpotNumber", 0) > 0:
                free_spots.append(spot_info)

        # Calculate distance and sort
        def calculate_distance(lat1, lon1, lat2, lon2):
            # Simple Euclidean distance for demonstration, use Haversine for real-world accuracy
            return ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5

        if user_latitude is None or user_longitude is None:
            return "User location (latitude and longitude) is required to find closest parking."

        if free_spots:
            for spot in free_spots:
                if spot.get("location") and isinstance(spot["location"], dict):
                    spot["distance"] = calculate_distance(
                        user_latitude, user_longitude,
                        spot["location"].get("latitude", 0), spot["location"].get("longitude", 0)
                    )
                else:
                    spot["distance"] = float('inf') # Set to infinity if location data is missing/malformed
            free_spots.sort(key=lambda s: s["distance"])
            closest_free = free_spots[0]
            response = (f"The closest free parking spot is '{closest_free['name']}' (ID: {closest_free['id']}) "
                        f"with {closest_free['availableSpotNumber']} spots available. "
                        f"It's approximately {closest_free['distance']:.2f} units away.")
            if len(free_spots) > 1:
                response += "\nOther free spots: " + ", ".join([
                    f"{s['name']} ({s['availableSpotNumber']} spots, {s['distance']:.2f} away)"
                    for s in free_spots[1:3] # List top 2 other free spots
                ])
            return response
        else:
            # If no free spots, sort all spots by proximity and suggest alternatives
            if all_spots:
                for spot in all_spots:
                    if spot.get("location") and isinstance(spot["location"], dict):
                        spot["distance"] = calculate_distance(
                            user_latitude, user_longitude,
                            spot["location"].get("latitude", 0), spot["location"].get("longitude", 0)
                        )
                    else:
                        spot["distance"] = float('inf')
                all_spots.sort(key=lambda s: s["distance"])
                response = "No free parking spots found near your location. "
                response += "Here are the closest parking spots, though they might be full or require payment:\n"
                for spot in all_spots[:3]: # List top 3 closest spots
                    response += (f"- '{spot['name']}' (ID: {spot['id']}): "
                                 f"{spot.get('availableSpotNumber', 'N/A')}/{spot.get('totalSpotNumber', 'N/A')} spots available, "
                                 f"approx {spot['distance']:.2f} units away.\n")
                return response
            else:
                return "No parking spots found in Fiware."

    @tool # Langchain tool decorator
    @staticmethod # Decorator to make it a static method
    def get_product_info(product_name: str) -> str:
        """
        Retrieves information about a specific product from Fiware.
        Prioritizes sale information if available.
        """
        url = f"{ORION_URL}/v2/entities"
        params = {
            "type": "Product",
            "q": f"name=={product_name}", # Case-sensitive search by name
            "options": "keyValues"
        }
        # Call the static method using the class name
        product_data = FiwareQueryTools.make_fiware_request(url, params)

        if not product_data:
            # Try case-insensitive search if direct match fails (optional but good for UX)
            params["q"] = f"name=~{product_name}"
            product_data = FiwareQueryTools.make_fiware_request(url, params)
            if not product_data:
                return f"Product '{product_name}' not found in Fiware."

        # Assuming there might be multiple products with similar names, take the first one or most relevant
        product = product_data[0]
        info = []

        # Prioritize sale information
        if product.get("onSale", False):
            info.append(f"GOOD NEWS! '{product.get('name', 'N/A')}' is currently ON SALE!")
            if product.get("salePrice"):
                info.append(f"Sale Price: {product['salePrice']} {product.get('currency', 'USD')}")

        info.append(f"Product Name: {product.get('name', 'N/A')}")
        info.append(f"Description: {product.get('description', 'N/A')}")
        info.append(f"Price: {product.get('price', 'N/A')} {product.get('currency', 'USD')}")
        info.append(f"Manufacturer: {product.get('manufacturer', 'N/A')}")
        info.append(f"Stock Quantity: {product.get('stockQuantity', 'N/A')}")
        info.append(f"Category: {product.get('category', 'N/A')}")

        return "\n".join(info)