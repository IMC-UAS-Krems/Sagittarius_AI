import json
import logging
from fiware_entity_fetcher import FiwareEntityFetcher # Import the class

# --- Basic Logging Setup for the main script ---
# Get the root logger or create a specific one for this script
# Using __name__ for the logger name is good practice
script_logger = logging.getLogger(__name__)
script_logger.setLevel(logging.INFO) # Set default logging level for the script

# This script might share handlers if already configured by imported modules,
# but explicitly add them if not to ensure output.
# Check if handlers are already attached to prevent duplicates
if not script_logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    script_logger.addHandler(console_handler)

    # File handler (optional, if you want a separate log for this script)
    file_handler = logging.FileHandler('app.log') # Or 'user_input.log'
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    script_logger.addHandler(file_handler)
# --- End Logging Setup ---


script_logger.info("--- Starting Get FIWARE Entity by ID Script ---")

# --- Configuration ---
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DATABASE = "orion"
MONGO_COLLECTION = "products" # Ensure this matches the collection where your entities are stored

script_logger.info(f"Configured to connect to MongoDB at {MONGO_HOST}:{MONGO_PORT}, database: {MONGO_DATABASE}, collection: {MONGO_COLLECTION}")

# --- Create Fetcher Instance ---
fetcher = FiwareEntityFetcher(
    host=MONGO_HOST,
    port=MONGO_PORT,
    database=MONGO_DATABASE,
    collection=MONGO_COLLECTION
)

# --- Get User Input ---
script_logger.info("Prompting user for entity ID.")
print("\nEnsure your MongoDB is running and contains entities in the "
      f"'{MONGO_DATABASE}.{MONGO_COLLECTION}' collection.")
entity_id_input = input("Enter the Entity ID to search for (e.g., 'urn:ngsi-ld:Product:001'): ")
script_logger.info(f"User entered ID: '{entity_id_input.strip()}'")

# --- Fetch and Display Entity ---
script_logger.info(f"Initiating fetch for entity with ID: '{entity_id_input.strip()}'...")
entity_data = fetcher.get_entity_by_id(entity_id_input.strip()) # .strip() to remove potential whitespace

if entity_data:
    script_logger.info("Entity data retrieved successfully.")
    print("\n--- Entity Found ---")
    print(json.dumps(entity_data, indent=4)) # Print raw JSON to console
else:
    script_logger.warning("Entity was not found or an error occurred during fetch.")
    print("\n--- Entity Not Found or Error ---")
    print("Please check the ID, MongoDB connection, and collection name.")

script_logger.info("--- Get FIWARE Entity by ID Script Finished ---")