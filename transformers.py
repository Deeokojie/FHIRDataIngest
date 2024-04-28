def transform_patient_data(patient_record):
    """
    Transforms a FHIR patient record into a tabular dictionary format.

    Args:
    patient_record (dict): A dictionary containing the FHIR patient record data.

    Returns:
    dict: A dictionary containing structured patient data.
    """
    if 'name' in patient_record and patient_record['name']:
        full_name = f"{patient_record['name'][0].get('given', [''])[0]} {patient_record['name'][0].get('family', '')}".strip()
    else:
        full_name = "Unknown"

    transformed_data = {
        "patient_id": patient_record.get("id", "Unknown"),
        "full_name": full_name,
        "birth_date": patient_record.get("birthDate", "Unknown"),
        "gender": patient_record.get("gender", "Unknown")
    }
    return transformed_data
