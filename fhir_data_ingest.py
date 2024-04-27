import json
import os
from pymongo import MongoClient 

client = MongoClient('mongodb://localhost:27017')
db = client['fhirData']

def determine_collection_name(filename):
            if "patients" in filename:
                return "patients"
            
            elif "encounters" in filename:
                return "encounters"
            
            elif "observations" in filename:
                return "observation"
            
            elif "procedure" in filename:
                return "procedure"
            
            elif "medication" in filename:
                return "medication"
            
            return "unknown"

def is_valid_data(data):
    required_fields = ['name', 'age', 'email']

    if not all(field in data for field in required_fields):
        return False
    if not isinstance(data['name'], str) or not isinstance(data['age'], int):
        return False
    return True
     

# Insert data from a file into a specified collection in MongoDB
def insert_data_from_file(filepath, collection_name):
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            valid_data = [item for item in data if is_valid_data(item)]
            if valid_data:
                db[collection_name].insert_many(valid_data)
                print(f"Inserted {len(valid_data)} records into {collection_name} from {filepath}")

            else:
                print(f"No valid data found in {filepath}")
    except json.JSONDecodeError as e:
        print(f"JSON error in file {filepath}: {e}")
    except MongoClient.errors.OperationFailure as e:
        print(f"Database error when inserting into {collection_name}: {e}")        
    except Exception as e:
        print(f"An error occurred while processing {filepath}: {e}")

data_directory = '/Applications/exa-data-eng-assessment/data'

# Loop over each file in the dir and insert into MongoDB
for filename in os.listdir(data_directory):
    if filename.endwith('.json'):
        file_path = os.path.join(data_directory, filename)

        collection_name = determine_collection_name(file_path)
        insert_data_from_file(file_path, collection_name)


