import csv
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
import os # For checking if file exists

# --- Basic Logging Setup ---
# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set default logging level for the module

# Create handlers
# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # Console will show INFO and above

# File handler
file_handler = logging.FileHandler('app.log') # Using a common log file for all scripts
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


class FiwareMongoImporter: # Renamed class
    """
    A class to connect to MongoDB and import data from a CSV file
    into a specified collection, compatible with potential FIWARE contexts.
    """

    def __init__(self, host="localhost", port=27017, database="orion", collection="products"):
        """
        Initializes the importer with MongoDB connection details.

        Args:
            host (str): The MongoDB host address. Defaults to "localhost".
            port (int): The MongoDB port number. Defaults to 27017.
            database (str): The name of the database to connect to. Defaults to "orion".
            collection (str): The name of the collection where data will be imported. Defaults to "products".
        """
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection
        self.client = None
        self.db = None
        self.mongo_collection = None
        self.logger = logger # Use the module-level logger

        self.logger.debug(f"FiwareMongoImporter instance initialized for {database}/{collection}")

    def _connect(self):
        """Establishes a connection to MongoDB and sets up the collection."""
        self.logger.info(f"Attempting to connect to MongoDB: {self.host}:{self.port}")
        try:
            self.client = MongoClient(host=self.host, port=self.port)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            self.db = self.client[self.database]
            self.mongo_collection = self.db[self.collection]
            self.logger.info(f"Successfully connected to MongoDB: {self.host}:{self.port}/{self.database}/{self.collection}")
            return True
        except ConnectionFailure as e:
            self.logger.error(f"Connection to MongoDB failed: {e}")
            self.cleanup()
            return False
        except PyMongoError as e:
            self.logger.error(f"An unexpected MongoDB error occurred during connection: {e}", exc_info=True)
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

    def import_csv(self, csv_file_path):
        """
        Reads a CSV file and imports each row as a document into the configured
        MongoDB collection.

        Args:
            csv_file_path (str): The absolute or relative path to the CSV file.

        Returns:
            bool: True if the import was successful, False otherwise.
        """
        self.logger.info(f"Starting CSV import process from '{csv_file_path}' to {self.database}.{self.collection}")

        if not os.path.exists(csv_file_path):
            self.logger.error(f"Error: CSV file not found at '{csv_file_path}'.")
            return False

        if not self._connect():
            self.logger.error("Failed to connect to MongoDB, cannot import CSV.")
            return False # Connection failed

        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                if not reader.fieldnames:
                    self.logger.warning("CSV file has no headers. Cannot import any data.")
                    return False

                headers = reader.fieldnames
                self.logger.info(f"CSV headers identified: {headers}")

                data_to_insert = []
                for i, row in enumerate(reader):
                    data_to_insert.append(row)
                    if (i + 1) % 1000 == 0: # Log progress every 1000 rows
                        self.logger.debug(f"Processed {i + 1} rows from CSV...")

                if data_to_insert:
                    self.logger.info(f"Prepared {len(data_to_insert)} records for insertion.")
                    result = self.mongo_collection.insert_many(data_to_insert)
                    self.logger.info(f"Successfully imported {len(result.inserted_ids)} records into "
                                     f"collection '{self.collection}' in database '{self.database}'.")
                    return True
                else:
                    self.logger.warning("CSV file is empty or has no data rows to import after reading.")
                    return False

        except FileNotFoundError: # Should be caught by os.path.exists, but good fallback
            self.logger.error(f"Error: CSV file not found at '{csv_file_path}'.", exc_info=True)
            return False
        except csv.Error as e:
            self.logger.error(f"Error reading CSV file '{csv_file_path}': {e}", exc_info=True)
            return False
        except PyMongoError as e:
            self.logger.error(f"A MongoDB error occurred during import: {e}", exc_info=True)
            return False
        except Exception as e:
            self.logger.critical(f"An unexpected critical error occurred during CSV import: {e}", exc_info=True)
            return False
        finally:
            self._disconnect() # Ensure connection is always closed

# Optional: Example of how you might test the class directly within this file
if __name__ == "__main__":
    logger.info("--- Testing FiwareMongoImporter directly (if executed as main) ---")

    TEST_CSV_PATH = "products-100000.csv"

    importer = FiwareMongoImporter( # Using the new class name
        host="localhost",
        port=27017,
        database="test_db",
        collection="test_products_csv_reanamed" # Example test collection
    )

    if importer.import_csv(TEST_CSV_PATH):
        logger.info(f"Direct test import of '{TEST_CSV_PATH}' successful!")
    else:
        logger.error(f"Direct test import of '{TEST_CSV_PATH}' failed.")

    logger.info("-------------------------------------------------------")