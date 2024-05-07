import json
import os
import logging
from pymongo import MongoClient, errors
from time import sleep

# Load database configuration from environment variables
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', 27017)
db_name = os.getenv('DB_NAME', 'test_database')

# Connect to MongoDB
client = MongoClient(f'mongodb://{db_host}:{db_port}/')
db = client[db_name]

# Configure logging to capture all events, saved to a log file with detailed time and level information.
logging.basicConfig(
    filename='data_ingest.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Load configuration settings from a JSON file to manage database connections and processing parameters.
def load_config():
    config_path ='/Users/test/Projects/FHIRDataIngest/config.json'
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}")
        return {}  

config = load_config()

# Function to establish a MongoDB client using the URI provided in the configuration file.
from pymongo import MongoClient, errors

def setup_mongo_client(use_test_db=False, use_ssl=False):
    try:
        db_name = config.get('test_database', 'fhirData') if use_test_db else config.get('database_name', 'fhirData')
        mongo_uri = config.get('mongo_uri', 'mongodb://localhost:27017')
        client = MongoClient('mongodb://localhost:27017/', tls=False)
    except errors.ConnectionFailure as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise ConnectionError("Failed to connect to the database")

def determine_collection_name(filename):
    if "patient" in filename:
        return "patients_collection"
    elif "encounter" in filename:
        return "encounters_collection"
    elif "observation" in filename:
        return "observations_collection"
    else:
        return "unknown_collection"

def transform_patient_data(patient_record):
    """
    Transforms a FHIR patient record into a tabular dictionary format.
    Args:
    patient_record (dict): A dictionary containing the FHIR patient record data.
    Returns:
    dict: A dictionary containing structured patient data.
    """
    try:
        patient_id = patient_record.get("id", "Unknown")
        name = patient_record.get('name', {})
        given_names = " ".join(name.get('given', []))
        family_name = name.get('family', "Unknown")
        birth_date = patient_record.get("birthDate", "Unknown")
        gender = patient_record.get("gender", "Unknown")

        full_name = f"{given_names} {family_name}".strip() if given_names and family_name else "Unknown"

        return {
            "patient_id": patient_id,
            "full_name": full_name,
            "birth_date": birth_date,
            "gender": gender
        }
    except IndexError as e:
        logging.error("Error processing patient record: Missing expected fields - %s", e)
        return None

def anonymize_data(patient_record):
    """
    Anonymizes sensitive patient data by replacing identifiable information with 'REDACTED'.

    Args:
        patient_record (dict): A dictionary containing the FHIR patient record data.

    Returns:
        dict: A dictionary with the sensitive data anonymized.
    """
    anonymized_record = {
        'id': patient_record.get('id', 'Unknown'),
        'name': {'family': 'REDACTED', 'given': ['REDACTED']},
        'birthDate': 'REDACTED',
        'gender': 'REDACTED',
        'address': [{'line': ['REDACTED'], 'city': 'REDACTED', 'state': 'REDACTED', 'postalCode': 'REDACTED', 'country': 'REDACTED'}]
    }
    return anonymized_record

def read_and_transform_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return transform_patient_data(data)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error with file {file_path}: {e}")
    return None

# Attempt to save a batch of transformed data to the database, with retry logic for handling failures.
def batch_save_to_database(data_batch, collection_name):
    if not data_batch:
        logging.info("No data to save; empty batch.")
        return
    try:
        collection = db[collection_name]
        collection.insert_many(data_batch)
        logging.info(f"Successfully saved batch to {collection_name}: {len(data_batch)} documents")
    except errors.BulkWriteError as e:
        logging.error(f"Bulk write error to {collection_name}: {e.details}")
    except errors.PyMongoError as e:
        logging.error(f"Failed to save batch to {collection_name}: {e}")
        raise

def log_unsaved_data(data_batch, collection_name):
    unsaved_data_file = f"unsaved_data_{collection_name}.log"
    with open(unsaved_data_file, 'a') as file:
        for record in data_batch:
            file.write(json.dumps(record) + '\n')
    logging.info(f"Logged unsaved documents to {unsaved_data_file}")
          
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

if __name__ == "__main__":
    db = setup_mongo_client(use_test_db=True)
    process_all_files(config['data_directory'], config['batch_size'])    