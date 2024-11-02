import random
import os
import uuid
import boto3
from datetime import date, timedelta
from sqlalchemy.orm import sessionmaker
from faker import Faker
from model import *
from random import randrange
import uuid


# Constants for the directory and S3 bucket
IMAGE_DIRECTORY = "/Users/andrew/Darwinist/darwinist-operator/prostate_jpeg"
S3_BUCKET = 'ee11f0132e5b'

# Initialize the S3 client
s3_client = boto3.client('s3')

# Initialize Faker for generating fake patient data
fake = Faker()

# Create a session from the configured Session class
session = Session()


def upload_image_to_s3(file_path):
    """Uploads the image to S3 and returns the S3 URI."""
    try:
        # Generate a random UUID for the file name
        file_name = f"{uuid.uuid4()}.jpg"
        s3_key = f"images/{file_name}"

        # Upload the file to S3
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)

        # Return the S3 URI of the uploaded file
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        return s3_uri

    except Exception as e:
        print(f"Error uploading {file_path} to S3: {e}")
        return None


def create_patients(num_patients):
    """Create and return a list of patients with images uploaded to S3."""
    patients = []
    for i in range(num_patients):
        image_path = os.path.join(IMAGE_DIRECTORY, f"{i}.jpg")

        # Upload the image to S3 and get the S3 URI
        s3_uri = upload_image_to_s3(image_path)
        
        if s3_uri is not None:
            patient = Patient(
                name=fake.name(),
                age=random.randint(18, 85),  # Random age between 18 and 85
                gender=random.choice(['Male', 'Female', 'Other']),
                medical_history=fake.sentence(),
                input_data_uri=s3_uri  # Store the S3 URI
            )
            patients.append(patient)

    session.add_all(patients)
    session.commit()
    return patients

def create_clinical_trial():
    """Create a new clinical trial and return the trial object."""
    trial = ClinicalTrial(
        trial_name="Trial {}".format(str(uuid.uuid4())[:8]),
        description="This is a trial created for testing 100 patients.",
        start_date=date.today(),
        trial_type="formal",
        product_id=random.randint(1, 29)  # Assuming there's a product with ID 1
    )
    session.add(trial)
    session.commit()
    return trial

def enroll_patients_in_trial(patients, trial):
    """Enroll the given patients into the specified trial."""
    enrollments = []
    for patient in patients:
        enrollment = TrialEnrollment(
            trial_id=trial.trial_id,
            patient_id=patient.patient_id,
            date_enrolled=date.today(),
            image_processing_job_id=None  # Set this if applicable
        )
        enrollments.append(enrollment)
    session.add_all(enrollments)
    session.commit()

def main():
    try:
        # Step 1: Create 100 patients
        patients = create_patients(10)
        print(f"Created {len(patients)} patients.")

        # Step 2: Create a new clinical trial
        trial = create_clinical_trial()
        print(f"Created clinical trial with ID: {trial.trial_id}")

        # Step 3: Enroll the patients in the clinical trial
        enroll_patients_in_trial(patients, trial)
        print(f"Enrolled {len(patients)} patients into trial ID {trial.trial_id}")

    except SQLAlchemyError as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()