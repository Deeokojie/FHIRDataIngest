FHIRDataIngest
Overview
This project transforms FHIR (Fast Healthcare Interoperability Resources) patient data into a tabular format and stores it in MongoDB. This process makes the data easier for analytics teams to create dashboards and visualizations.

Technologies Used
Programming Language: Python 3.8+
Database: MongoDB
Libraries: PyMongo, Flask (optional, for API)
Testing: Python’s unittest for unit and performance tests
Deployment: Docker (Optional)
Getting Started
Prerequisites
Python 3.8 or higher
MongoDB (running locally or accessible via the network)
Installation
Clone the repository:

git clone https://github.com/Deeokojie/FHIRDataIngest.git
cd FHIRDataIngest
Create a virtual environment and activate it:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install required Python packages:

pip install -r requirements.txt
Configuration
Create a config.json file in the project root directory with the following fields:

{
  "mongo_uri": "mongodb://localhost:27017",
  "database_name": "fhirData",
  "batch_size": 100,
  "data_directory": "/path/to/data/files"
}
This will set up the connection to MongoDB and specify the data directory.

Optionally, you can use environment variables to override MongoDB settings:

export DB_HOST='localhost'
export DB_PORT=27017
Running the Application
To start processing the data, run the following command:

python fhir_data_ingest.py
This will ingest FHIR data, transform it into a tabular format, and store it in MongoDB.

Running the Tests
To run the unit and performance tests:

python -m unittest
This will execute the full suite of tests, including tests for transforming FHIR data and performance benchmarks.

Docker Deployment
To deploy this application using Docker, follow these steps:

Build the Docker image:

docker build -t fhir_data_ingest .
Run the Docker container:

docker run -d --name fhir_data_ingest -p 27017:27017 fhir_data_ingest
Verify that MongoDB is running in the container:

docker exec -it fhir_data_ingest mongo --eval 'db.runCommand({ connectionStatus: 1 })'
Dockerfile (Create this in your project root if it doesn’t exist):
Dockerfile
Copy code

# Use official Python image as a base image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the app
CMD ["python", "fhir_data_ingest.py"]
Architecture Overview
The data pipeline is designed to transform healthcare data from the FHIR format into a more analytics-friendly tabular format. Major components include:

Data Ingestion: Receives FHIR data in JSON format from external sources.
Transformation: Converts raw FHIR data into a structured schema.
Storage: Loads the transformed data into MongoDB.
Testing: Comprehensive unit, integration, and performance tests are included to ensure robustness.

Next Steps
Future improvements include:

Enhanced security: Field-level encryption for sensitive data in MongoDB.
Real-time processing: Adding streaming frameworks like Apache Kafka for real-time data handling.

Conclusion
With the steps outlined above, you can deploy, test, and scale the FHIR data ingestion system, making it a valuable asset for healthcare analytics teams. Further enhancements, such as real-time processing and better security, can be incorporated as the system evolves.
