import requests
from faker import Faker
import random
from datetime import datetime

# Initialize Faker to generate random data
faker = Faker()

# Base URL for your Flask API
BASE_URL = "http://127.0.0.1:5000/api"

# Helper function to generate random clinical trial data
def create_random_clinical_trial(product_id):
    start_date = faker.date_between(start_date="-2y", end_date="today")
    end_date = faker.date_between(start_date=start_date, end_date="+1y")
    trial_data = {
        "TrialName": faker.catch_phrase(),
        "Description": faker.text(),
        "StartDate": start_date.strftime('%Y-%m-%d'),
        "EndDate": end_date.strftime('%Y-%m-%d'),
        "TrialType": random.choice(['formal', 'informal']),
        "ProductID": product_id
    }
    return trial_data

# Helper function to create random patient data
def create_random_patient():
    patient_data = {
        "Name": faker.name(),
        "Age": random.randint(18, 85),
        "Gender": random.choice(['Male', 'Female', 'Other']),
        "MedicalHistory": faker.text(),
    }
    return patient_data

# Helper function to enroll a patient in a trial
def create_random_enrollment(trial_id, patient_id):
    enrollment_data = {
        "PatientID": patient_id
    }
    return enrollment_data

# Helper function to record trial results
def create_random_trial_result():
    result_data = {
        "Outcome": random.choice(['Success', 'Failure', 'Ongoing']),
        "AdditionalData": faker.text()
    }
    return result_data

# Function to inject random clinical trials into the API
def inject_clinical_trials(product_id, num_trials=5):
    for _ in range(num_trials):
        trial_data = create_random_clinical_trial(product_id)
        response = requests.post(f"{BASE_URL}/trials", json=trial_data)
        if response.status_code == 201:
            trial_id = response.json().get("TrialID")
            print(f"Successfully created trial with ID: {trial_id}")
        else:
            print(f"Failed to create trial: {response.status_code}, {response.text}")

# Function to inject random patients into the API
def inject_patients(num_patients=10):
    patient_ids = []
    for _ in range(num_patients):
        patient_data = create_random_patient()
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        if response.status_code == 201:
            patient_id = response.json().get("PatientID")
            patient_ids.append(patient_id)
            print(f"Successfully created patient with ID: {patient_id}")
        else:
            print(f"Failed to create patient: {response.status_code}, {response.text}")
    return patient_ids

# Function to enroll patients in a clinical trial
def enroll_patients_in_trial(trial_id, patient_ids):
    for patient_id in patient_ids:
        enrollment_data = create_random_enrollment(trial_id, patient_id)
        response = requests.post(f"{BASE_URL}/trials/{trial_id}/enroll", json=enrollment_data)
        if response.status_code == 201:
            print(f"Successfully enrolled patient {patient_id} in trial {trial_id}")
        else:
            print(f"Failed to enroll patient: {response.status_code}, {response.text}")

# Function to record trial results for enrolled patients
def record_trial_results(enrollment_id):
    result_data = create_random_trial_result()
    response = requests.post(f"{BASE_URL}/enrollments/{enrollment_id}/results", json=result_data)
    if response.status_code == 201:
        print(f"Successfully recorded trial result for enrollment {enrollment_id}")
    else:
        print(f"Failed to record trial result: {response.status_code}, {response.text}")

# Main function to run all the steps
def inject_data():
    # Assuming there's an existing product in the database
    product_id = "93f00946-0ff8-4b22-a5b6-290e90fe64d5"  # Replace with an actual product ID

    # Inject clinical trials
    inject_clinical_trials(product_id, num_trials=5)

    # Inject patients
    patient_ids = inject_patients(num_patients=10)

    # Enroll patients in a trial (assuming trial ID 1 exists)
    trial_id = 1  # Replace with an actual trial ID
    enroll_patients_in_trial(trial_id, patient_ids)

if __name__ == "__main__":
    inject_data()