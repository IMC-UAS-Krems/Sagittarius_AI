import json
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

# --- Basic Logging Setup (can be configured more elaborately) ---
# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set default logging level for the module

# Create handlers
# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # Console will show INFO and above

# File handler
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG) # File will capture all DEBUG and above

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
if not logger.handlers: # Avoid adding handlers multiple times if module is reloaded
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
# --- End Logging Setup ---


class FiwareEntityFetcher:
    """
    A class to connect to MongoDB and fetch a single entity by its ID,
    primarily designed for databases used by Orion Context Broker.
    """

    def __init__(self, host="localhost", port=27017, database="orion", collection="products"):
        """
        Initializes the fetcher with MongoDB connection details.
        Also sets up a logger specific to this instance if needed, or uses the module logger.

        Args:
            host (str): The MongoDB host address. Defaults to "localhost".
            port (int): The MongoDB port number. Defaults to 27017.
            database (str): The MongoDB database name (e.g., "orion"). Defaults to "orion".
            collection (str): The MongoDB collection name containing entities (e.g., "products"). Defaults to "products".
        """
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection
        self.client = None
        self.db = None
        self.entities_collection = None
        self.logger = logger # Use the module-level logger

        self.logger.debug(f"FiwareEntityFetcher instance initialized for {database}/{collection}")

    def _connect(self):
        """Establishes a connection to MongoDB."""
        self.logger.info(f"Attempting to connect to MongoDB: {self.host}:{self.port}")
        try:
            self.client = MongoClient(host=self.host, port=self.port)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            self.db = self.client[self.database]
            self.entities_collection = self.db[self.collection]
            self.logger.info(f"Successfully connected to MongoDB: {self.host}:{self.port}/{self.database}/{self.collection}")
            return True
        except ConnectionFailure as e:
            self.logger.error(f"Connection to MongoDB failed: {e}")
            self.cleanup()
            return False
        except PyMongoError as e:
            self.logger.error(f"An unexpected MongoDB error occurred during connection: {e}")
            self.cleanup()
            return False
        except Exception as e:
            self.logger.critical(f"A critical error occurred during MongoDB connection: {e}", exc_info=True)
            self.cleanup()
            return False

    def _disconnect(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed.")
        else:
            self.logger.debug("No active MongoDB client to close.")

    def cleanup(self):
        """Public method to ensure MongoDB connection is closed."""
        self._disconnect()

    def get_entity_by_id(self, entity_id):
        """
        Fetches a single entity from the configured MongoDB collection by its _id.

        Args:
            entity_id (str): The _id of the entity to retrieve.

        Returns:
            dict or None: The entity document if found, otherwise None.
        """
        self.logger.info(f"Attempting to fetch entity with ID: '{entity_id}' from {self.database}.{self.collection}")
        if not self._connect():
            self.logger.error("Failed to connect to MongoDB, cannot fetch entity.")
            return None # Connection failed

        try:
            entity = self.entities_collection.find_one({"_id": entity_id})
            if entity:
                self.logger.info(f"Entity with ID '{entity_id}' found.")
                # self.logger.debug(f"Fetched entity data: {json.dumps(entity, indent=4)}") # Log full data if needed for debug
                return entity
            else:
                self.logger.warning(f"No entity found with ID '{entity_id}'.")
                return None
        except PyMongoError as e:
            self.logger.error(f"A MongoDB error occurred while fetching entity with ID '{entity_id}': {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.critical(f"A critical error occurred while fetching entity with ID '{entity_id}': {e}", exc_info=True)
            return None
        finally:
            self._disconnect() # Ensure connection is always closed

# Optional: Example of how you might test the class directly within this file
if __name__ == "__main__":
    logger.info("--- Testing FiwareEntityFetcher directly (if executed as main) ---")

    fetcher = FiwareEntityFetcher(
        host="localhost",
        port=27017,
        database="orion",
        collection="products" # Or 'entities' depending on your setup
    )

    # Replace with an actual ID from your 'products' collection if you have one
    # If not, run your CSV import script first to populate the database
    test_id = "urn:ngsi-ld:Product:001" # Example ID

    logger.info(f"\nAttempting to fetch entity with ID: {test_id}")
    fetched_entity = fetcher.get_entity_by_id(test_id)

    if fetched_entity:
        logger.info("Fetched Entity Details:")
        # For console output, still use print or a dedicated logger for displaying data
        print(json.dumps(fetched_entity, indent=4))
    else:
        logger.warning("Test entity not found or an error occurred during fetch.")

    logger.info("-------------------------------------------------------")