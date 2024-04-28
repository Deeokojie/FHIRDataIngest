import unittest
from transformers import transform_patient_data

class TestTransformPatientData(unittest.TestCase):
    # Test the transformation of FHIR patient records into tabular format

    def test_transform_patient_data_basic(self):
        # Testing basic functionality
        patient_record = {
            "id": "123",
            "name": [{"given": ["John"], "family": "Doe"}],
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

    def test_missing_fields(self):
        # Testing with missing fields
        patient_record = {
            "id": "123",
            "name": [{"given": ["John"]}],  # Missing 'family' name
            "gender": "male"
        }
        expected_output = {
            "patient_id": "123",
            "full_name": "John ",  # Check how your function handles missing family name
            "birth_date": "Unknown",  # Assuming default for missing birthDate is 'Unknown'
            "gender": "male"
        }
        result = transform_patient_data(patient_record)
        self.assertEqual(result, expected_output)

    def test_incorrect_data_types(self):
        # Testing with incorrect data types (e.g., numbers instead of strings)
        patient_record = {
            "id": 123,  # ID as number
            "name": [{"given": [123], "family": 456}],  # Numbers instead of strings
            "birthDate": "1980-01-01",
            "gender": "male"
        }
        with self.assertRaises(TypeError):  # Assuming your function raises TypeError for wrong data types
            transform_patient_data(patient_record)

if __name__ == '__main__':
    unittest.main()

