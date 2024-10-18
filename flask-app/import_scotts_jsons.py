import os
import json
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import model

def import_json_files(directory):
    # Start a new session
    session = model.Session()

    # Iterate over files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            print(f'Processing {filepath}')
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Process the JSON data
                try:
                    process_data(data, session)
                except Exception as e:
                    print(f'Error processing {filename}: {e}')
                    session.rollback()
    # Commit the session
    session.commit()
    session.close()

def process_data(data, session):
    # Map JSON data to models
    # Process the vendor
    vendor_id = data.get('VendorID')
    vendor_name = data.get('VendorName')
    contact_email = data.get('ContactEmail')
    website = data.get('Website')

    # Check if the vendor already exists
    vendor = session.query(model.Vendor).filter_by(VendorID=vendor_id).first()
    if not vendor:
        vendor = model.Vendor(
            VendorID=vendor_id,
            VendorName=vendor_name,
            ContactEmail=contact_email,
            Website=website
        )
        session.add(vendor)
        session.flush()  # To get the VendorID if it's generated
    else:
        # Update existing vendor details if needed
        vendor.VendorName = vendor_name
        vendor.ContactEmail = contact_email
        vendor.Website = website

    # Process the products
    products = data.get('products', [])
    for product_data in products:
        product_id = product_data.get('ProductID')
        product_name = product_data.get('ProductName')
        description = product_data.get('Description')
        dicom_output = product_data.get('DICOMOutput')
        # Convert boolean if necessary
        dicom_output = True if dicom_output in [True, 'True', 'true', 1] else False

        # Check if the product already exists
        product = session.query(model.Product).filter_by(ProductID=product_id).first()
        if not product:
            product = model.Product(
                ProductID=product_id,
                ProductName=product_name,
                Description=description,
                DICOMOutput=dicom_output,
                VendorID=vendor.VendorID
            )
            session.add(product)
            session.flush()
        else:
            # Update existing product details if needed
            product.ProductName = product_name
            product.Description = description
            product.DICOMOutput = dicom_output
            product.VendorID = vendor.VendorID

        # Process regulatory approved pathologies
        pathologies = product_data.get('regulatory_approved_pathologies', [])
        for pathology_data in pathologies:
            pathology_name = pathology_data.get('name')
            modality = pathology_data.get('modality')
            body_part = pathology_data.get('body_part')
            # Create a unique pathology name
            pathology_full_name = f"{pathology_name} ({modality}, {body_part})"
            # Check if the pathology already exists
            pathology = session.query(model.Pathology).filter_by(PathologyName=pathology_full_name).first()
            if not pathology:
                pathology = model.Pathology(
                    PathologyID=str(uuid.uuid4()),
                    PathologyName=pathology_full_name
                )
                session.add(pathology)
                session.flush()

            # Create or get ProductPathology association
            product_pathology = session.query(model.ProductPathology).filter_by(
                ProductID=product.ProductID,
                PathologyID=pathology.PathologyID
            ).first()
            if not product_pathology:
                product_pathology = model.ProductPathology(
                    ProductID=product.ProductID,
                    PathologyID=pathology.PathologyID,
                    UseCase=None  # UseCase is not specified in the data
                )
                session.add(product_pathology)

            # Process approvals
            approvals = pathology_data.get('approved_by', [])
            for approval_data in approvals:
                authority = approval_data.get('authority')
                approval_date = approval_data.get('approval_date')
                approval_id = approval_data.get('id')

                # Convert approval_date to date object
                approval_date_obj = datetime.datetime.strptime(approval_date, '%Y-%m-%d').date()

                # Check if the approval already exists
                approval = session.query(model.RegulatoryApproval).filter_by(
                    ApprovedBy=authority,
                    ApprovalDate=approval_date_obj,
                    ProductID=product.ProductID,
                    PathologyID=pathology.PathologyID
                ).first()
                if not approval:
                    approval = model.RegulatoryApproval(
                        ApprovalStatus='Approved',
                        ApprovalDate=approval_date_obj,
                        ApprovedBy=authority,
                        ProductID=product.ProductID,
                        PathologyID=pathology.PathologyID
                    )
                    session.add(approval)
    # Commit after processing each vendor
    session.commit()

if __name__ == '__main__':
    directory = '/Users/andrew/Library/CloudStorage/GoogleDrive-andrew@darwinist.io/Shared drives/Assets/vendor-jsons'  # Replace with the path to your JSON files directory
    import_json_files(directory)