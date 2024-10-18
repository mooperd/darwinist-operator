import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from model import *
import os


# Assuming the engine has already been defined and is connected to your database
session = Session
create_all()

def load_data(data):
    try:
        # Create a new vendor
        vendor = Vendor(
            vendor_name=data['VendorName'],
            contact_email=data['ContactEmail'],
            website=data['Website']
        )
        session.add(vendor)
        session.flush()  # Ensures vendor_id is available

        # Process the products
        for product_data in data['products']:
            product = Product(
                product_name=product_data['product_name'],
                description=product_data['Description'],
                dicom_output=product_data['DICOMOutput'],
                vendor_id=vendor.vendor_id
            )
            session.add(product)
            session.flush()  # Ensures product_id is available

            # Process the regulatory approvals for pathologies
            for pathology_data in product_data['regulatory_approved_pathologies']:
                # Ensure the Pathology, Modality, and BodyPart entries exist or create them
                pathology = session.query(Pathology).filter_by(name=pathology_data['name']).first()
                if not pathology:
                    pathology = Pathology(name=pathology_data['name'])
                    session.add(pathology)
                    session.flush()

                modality = session.query(Modality).filter_by(name=pathology_data['modality']).first()
                if not modality:
                    modality = Modality(name=pathology_data['modality'])
                    session.add(modality)
                    session.flush()

                body_part = session.query(BodyPart).filter_by(name=pathology_data['body_part']).first()
                if not body_part:
                    body_part = BodyPart(name=pathology_data['body_part'])
                    session.add(body_part)
                    session.flush()

                # Process each regulatory approval
                for approval_data in pathology_data['approved_by']:
                    regulatory_body = session.query(RegulatoryBody).filter_by(name=approval_data['authority']).first()
                    if not regulatory_body:
                        regulatory_body = RegulatoryBody(name=approval_data['authority'])
                        session.add(regulatory_body)
                        session.flush()

                    # Create the approval record
                    approval = Approval(
                        approval_date=approval_data['approval_date'],
                        id_code=approval_data['id'],
                        approval_status=bool(approval_data['approval_date']),  # True if there is an approval date
                        product_id=product.product_id,
                        pathology_id=pathology.pathology_id,
                        modality_id=modality.modality_id,
                        body_part_id=body_part.body_part_id,
                        regulatory_body_id=regulatory_body.regulatory_body_id
                    )
                    session.add(approval)

        # Commit the session
        print("committing")
        session.commit()

    except SQLAlchemyError as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


# Function to process all JSON files in a directory
def load_data_from_directory(directory_path):
    # Get a list of all JSON files in the directory
    json_files = [file for file in os.listdir(directory_path) if file.endswith('.json')]

    # Iterate through each file
    for json_file in json_files:
        file_path = "{}/{}".format(directory_path, json_file)
        print(file_path)
        print(f"Processing file: {file_path}")

        # Open and load the JSON data
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Call load_data to insert this JSON data into the database
        load_data(data)

# Define the path to your directory containing JSON files
directory_path = "/Users/andrew/Library/CloudStorage/GoogleDrive-andrew@darwinist.io/Shared drives/Assets/vendor-jsons"

# Load all JSON files from the directory into the database
load_data_from_directory(directory_path)