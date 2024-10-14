import requests
from faker import Faker
import random
from datetime import datetime

# Initialize Faker to generate random data
faker = Faker()

# Base URL of your Flask API
BASE_URL = 'http://127.0.0.1:5000/api/vendors'

def create_random_vendor():
    # Create random vendor data
    vendor_id = faker.uuid4()
    vendor_name = faker.company()
    contact_email = faker.email()
    vendor_address = faker.address()
    website = faker.url()

    # Create random product data for the vendor
    products = []
    for _ in range(random.randint(1, 3)):  # Create 1 to 3 products per vendor
        product_id = faker.uuid4()
        product_name = faker.catch_phrase()
        description = faker.text()
        results_displayed_in_ids7 = random.choice([True, False])
        dicom_output = faker.word()
        worklist_integration = random.choice([True, False])
        prepopulated_reports = random.choice([True, False])

        # Create random pathology and regulatory approval data for the product
        regulatory_approved_pathologies = []
        for _ in range(random.randint(1, 2)):  # 1-2 regulatory approvals per product
            pathology_id = faker.uuid4()
            pathology_name = faker.word()
            approval_status = random.choice(['approved', 'pending', 'rejected'])
            approval_date = faker.date_this_decade().isoformat()
            approved_by = faker.company()

            regulatory_approved_pathologies.append({
                'id': pathology_id,
                'name': pathology_name,
                'approval_status': approval_status,
                'approval_date': approval_date,
                'approved_by': approved_by
            })

        product_data = {
            'id': product_id,
            'name': product_name,
            'description': description,
            'results_displayed_in_IDS7': results_displayed_in_ids7,
            'DICOM_output': dicom_output,
            'Worklist_integration': worklist_integration,
            'pre-populated-reports': prepopulated_reports,
            'regulatory_approved_pathologies': regulatory_approved_pathologies
        }
        products.append(product_data)

    vendor_data = {
        'vendor': {
            'id': vendor_id,
            'name': vendor_name,
            'contact_email': contact_email,
            'website': website,
            'products': products
        }
    }

    return vendor_data

def inject_random_data(num_vendors=5):
    # Inject random vendor data into the API
    for _ in range(num_vendors):
        vendor_data = create_random_vendor()
        response = requests.post(BASE_URL, json=vendor_data)
        
        if response.status_code == 201:
            print(f"Successfully created vendor: {vendor_data['vendor']['name']}")
        else:
            print(f"Failed to create vendor: {response.status_code}, {response.text}")

if __name__ == "__main__":
    # Inject random data into the API
    inject_random_data(num_vendors=5)