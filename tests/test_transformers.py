import os
import sys
import json
import time 
import unittest
import logging
import ssl
import mongomock
import threading
from unittest.mock import patch
from pymongo import MongoClient, errors
from pymongo.ssl_support import CERT_NONE 
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError 
from ..fhir_transformers import transform_patient_data, anonymize_data, db
from ..fhir_transformers import process_all_files

logging.basicConfig(level=logging.DEBUG)
print("Python Path:", sys.path)

# MongoDB URI including username, password, and the authSource
uri = "mongodb://username:password@localhost:27017/test_database?authSource=admin&ssl=true"

# Create a MongoDB client with TLS/SSL
client = MongoClient(uri, ssl_certfile='/Users/test/Projects/FHIRDataIngest/combined.pem', ssl_cert_reqs=ssl.CERT_NONE)

db = client['test_database']

def load_config():
    config_path = 'config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    else:
        raise Exception("Configuration file not found")

class DatabaseTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up MongoDB connection once for all tests in this class."""
        cls.config = load_config()
        cls.client = cls.get_mongo_client(cls.config)
        cls.db = cls.client[cls.config.get('database_name', 'test_database')]

    @classmethod
    def tearDownClass(cls):
        """Clean up the database after tests."""
        cls.client.close()
        try:
            cls.client.drop_database(cls.config.get('database_name', 'test_database'))
        except Exception as e:
            logging.error(f"Failed to drop database: {e}")

    @classmethod
    def get_mongo_client(cls, config):
        """Create a MongoDB client using the provided configuration."""
        mongo_uri = config.get('mongo_uri', 'mongodb://localhost:27017/')
        return MongoClient(
            mongo_uri,
            ssl=config.get('use_ssl', False),
            username=config.get('username'),
            password=config.get('password'),
            authSource=config.get('auth_database', 'admin'),
            ssl_cert_reqs=ssl.CERT_NONE
        )
    
class TransformPatientDataTests(DatabaseTestBase):
    """Tests for transforming FHIR patient records into tabular format."""

    @classmethod
    def populate_test_data(cls, db):
        """Populates test data in the database."""
        try:
            db.patients.insert_one({
                "_id": "8c95253e-8ee8-9ae8-6d40-021d702dc78e",
                "name": {"family": "Dickens475", "given": ["Aaron697"]},
                "birthDate": "1944-08-28",
                "gender": "male"
            })
            db.encounters.insert_one({
                "_id": "4dbc90e0-b7b2-482c-24af-1405654e59ae",
                "status": "finished",
                "type": "General examination of patient",
                "patient_id": "8c95253e-8ee8-9ae8-6d40-021d702dc78e"
            })
        except Exception as e:
            logging.error(f"Error populating test data: {e}")
            raise

    def test_transform_valid_patient_data(self):
        """Tests transformation logic correctness."""
        patient_record = {
            "id": "123",
            "name": {"given": ["John"], "family": "Doe"},
            "birthDate": "1980-01-01",
            "gender": "male"
        }
        expected_output = {
            "patient_id": "123",
            "full_name": "John Doe",
            "birth_date": "1980-01-01",
            "gender": "male"
        }
        result = transform_patient_data(patient_record)
        self.assertEqual(result, expected_output)

        
class DatabaseTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = MongoClient('mongodb://localhost:27017/')
        cls.db = cls.client['test_database']

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        try:
            cls.client.drop_database('test_database')
        except Exception as e:
            logging.error(f"Failed to drop database: {e}")

class TransformPatientDataTests(DatabaseTestBase):
    def test_transform_valid_patient_data(self):
        """Tests transformation logic correctness."""
        patient_record = {
            "id": "123",
            "name": {"given": ["John"], "family": "Doe"},
            "birthDate": "1980-01-01",
            "gender": "male"
        }
        expected_output = {
            "patient_id": "123",
            "full_name": "John Doe",
            "birth_date": "1980-01-01",
            "gender": "male"
        }
        result = transform_patient_data(patient_record)
        self.assertEqual(result, expected_output)

class PerformanceTests(DatabaseTestBase):
    def test_data_transformation_performance(self):
        """Test the speed of transforming FHIR data into tabular format."""
        start_time = time.time()
        for _ in range(1000):
            data = {"id": str(_), "name": {"given": ["John"], "family": "Doe"}, "birthDate": "1980-01-01", "gender": "male"}
            transform_patient_data(data)
        end_time = time.time()
        self.assertLess(end_time - start_time, 10, "Data transformation for 1000 records should take less than 10 seconds")

if __name__ == '__main__':
    unittest.main()
