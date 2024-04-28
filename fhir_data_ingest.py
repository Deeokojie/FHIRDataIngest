import json
import os
import logging
from pymongo import MongoClient, errors
from time import sleep

# Import the function that transforms raw FHIR patient data into a structured dictionary.
from transformers import transform_patient_data

# Configure logging to capture all events, saved to a log file with detailed time and level information.
logging.basicConfig(
    filename='data_ingest.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Load configuration settings from a JSON file to manage database connections and processing parameters.
def load_config():
    try:
        with open('config.json', 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise

config = load_config()

# Establish a MongoDB client using the URI provided in the configuration file.
def setup_mongo_client():
    try:
        client = MongoClient(config['mongo_uri'])
        return client[config['database_name']]
    except errors.ConnectionFailure as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise

db = setup_mongo_client()

# Read JSON data from a file, transform it using a custom function, and handle errors gracefully.
def read_and_transform_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return transform_patient_data(data)
    except Exception as e:
        logging.error(f"Error with file {file_path}: {e}")
        return None

# Attempt to save a batch of transformed data to the database, with retry logic for handling failures.
def batch_save_to_database(data_batch, collection_name):
    if not data_batch:
        return
    retry_count = 0
    max_retries = config.get('max_retry_attempts', 3)
    delay_seconds = config.get('retry_delay_seconds', 5)
    while retry_count < max_retries:
        try:
            collection = db[collection_name]
            collection.insert_many(data_batch)
            logging.info(f"Batch saved to {collection_name}. Total documents: {len(data_batch)}")
            break
        except errors.PyMongoError as e:
            logging.error(f"Failed to save batch to {collection_name}: {e}")
            retry_count += 1
            logging.info(f"Retrying batch save ({retry_count}/{max_retries}) after a delay...")
            sleep(delay_seconds)
    else:
        logging.error("Max retry attempts reached. Data not saved.")

# Process all files in a specified directory, transforming and saving them in batches to the database.
def process_all_files(directory, batch_size):
    if not os.path.exists(directory):
        logging.error(f"Data directory does not exist: {directory}")
        return

    files_processed = 0
    data_batch = []
    collection_name = ""

    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            new_collection_name = determine_collection_name(filename)
            
            # Save the current batch before switching to a new collection if necessary.
            if new_collection_name != collection_name and data_batch:
                batch_save_to_database(data_batch, collection_name)
                data_batch = []
            
            collection_name = new_collection_name
            transformed_data = read_and_transform_data(file_path)
            
            if transformed_data:
                data_batch.append(transformed_data)
                if len(data_batch) >= batch_size:
                    batch_save_to_database(data_batch, collection_name)
                    data_batch = []
            
            files_processed += 1

    # Ensure any remaining data is saved after all files have been processed.
    if data_batch:
        batch_save_to_database(data_batch, collection_name)

    logging.info(f"Total files processed: {files_processed}")

# Determine the appropriate MongoDB collection based on filename patterns, supporting various data types.
def determine_collection_name(filename):
    mapping = {
        "patients": "patients",
        "encounters": "encounters",
        "observations": "observation",
        "procedure": "procedures",
        "medication": "medications"
    }
    for key, value in mapping.items():
        if key in filename:
            return value
    logging.warning(f"Unknown file type for {filename}. Defaulting to 'unknown' collection.")
    return "unknown"

if __name__ == "__main__":
    process_all_files(config['data_directory'], config['batch_size'])
