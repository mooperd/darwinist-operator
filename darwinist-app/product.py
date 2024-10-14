from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import secrets
from model import *
from app import app
import traceback
from datetime import datetime

## API endpoints
## Create API Endpoint
@app.route('/api/vendors', methods=['POST'])
def create_vendor_api():
    session = Session
    data = request.get_json()
    try:
        # Extract vendor data
        vendor_data = data.get('vendor')
        if not vendor_data:
            abort(400, description="No vendor data provided")

        # Check if vendor exists
        vendor = session.query(Vendor).filter_by(VendorID=vendor_data['id']).first()
        if not vendor:
            vendor = Vendor(
                VendorID=vendor_data['id'],
                VendorName=vendor_data['name'],
                ContactEmail=vendor_data.get('contact_email'),
                Website=vendor_data.get('website')
            )
            session.add(vendor)
            session.commit()

        # Process products
        for product_data in vendor_data.get('products', []):
            # Check if product exists
            product = session.query(Product).filter_by(ProductID=product_data['id']).first()
            if not product:
                product = Product(
                    ProductID=product_data['id'],
                    ProductName=product_data['name'],
                    Description=product_data.get('description'),
                    ResultsDisplayedInIDS7=product_data.get('results_displayed_in_IDS7'),
                    DICOMOutput=product_data.get('DICOM_output'),
                    WorklistIntegration=product_data.get('Worklist_integration'),
                    PrePopulatedReports=product_data.get('pre-populated-reports'),
                    VendorID=vendor.VendorID,
                    vendor_=vendor
                )
                session.add(product)
                session.commit()
            # Process pathologies and approvals
            for pathology_data in product_data.get('regulatory_approved_pathologies', []):
                # Check if pathology exists
                pathology = session.query(Pathology).filter_by(PathologyID=pathology_data['id']).first()
                if not pathology:
                    pathology = Pathology(
                        PathologyID=pathology_data['id'],
                        PathologyName=pathology_data['name']
                    )
                    session.add(pathology)
                    session.commit()
                # Associate product with pathology
                product_pathology = session.query(ProductPathology).filter_by(
                    ProductID=product.ProductID,
                    PathologyID=pathology.PathologyID
                ).first()
                if not product_pathology:
                    product_pathology = ProductPathology(
                        ProductID=product.ProductID,
                        PathologyID=pathology.PathologyID,
                        product=product,
                        pathology=pathology
                    )
                    session.add(product_pathology)
                    session.commit()
                # Add regulatory approval
                approval_date = date.fromisoformat(pathology_data['approval_date'])
                approval = RegulatoryApproval(
                    ApprovalStatus=pathology_data.get('approval_status'),
                    ApprovalDate=approval_date,
                    ApprovedBy=pathology_data.get('approved_by'),
                    ProductID=product.ProductID,
                    PathologyID=pathology.PathologyID
                )
                session.add(approval)
                session.commit()
        return jsonify({"message": "Data uploaded successfully"}), 201
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))
    except Exception as e:
        session.rollback()
        abort(500, description=str(e))


## Get All Vendors API Endpoint
@app.route('/api/vendors', methods=['GET'])
def get_vendors_api():
    session = Session
    try:
        vendors = session.query(Vendor).all()
        result = []
        for vendor in vendors:
            vendor_data = {
                'VendorID': vendor.VendorID,
                'VendorName': vendor.VendorName,
                'ContactEmail': vendor.ContactEmail,
                'Website': vendor.Website,
                'products': []
            }
            for product in vendor.products:
                product_data = {
                    'ProductID': product.ProductID,
                    'ProductName': product.ProductName,
                    'Description': product.Description,
                    'ResultsDisplayedInIDS7': product.ResultsDisplayedInIDS7,
                    'DICOMOutput': product.DICOMOutput,
                    'WorklistIntegration': product.WorklistIntegration,
                    'PrePopulatedReports': product.PrePopulatedReports,
                    'regulatory_approved_pathologies': []
                }
                # Add pathologies and approvals
                for approval in product.approvals:
                    pathology = session.query(Pathology).filter_by(PathologyID=approval.PathologyID).first()
                    pathology_data = {
                        'id': pathology.PathologyID,
                        'name': pathology.PathologyName,
                        'approval_status': approval.ApprovalStatus,
                        'approval_date': approval.ApprovalDate.isoformat(),
                        'approved_by': approval.ApprovedBy
                    }
                    product_data['regulatory_approved_pathologies'].append(pathology_data)
                vendor_data['products'].append(product_data)
            result.append(vendor_data)
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=str(e))


## Get a Specific Vendor API endpoint
@app.route('/api/vendors/<vendor_id>', methods=['GET'])
def get_vendor_api(vendor_id):
    session = Session
    try:
        vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
        if not vendor:
            abort(404, description="Vendor not found")
        vendor_data = {
            'VendorID': vendor.VendorID,
            'VendorName': vendor.VendorName,
            'ContactEmail': vendor.ContactEmail,
            'Website': vendor.Website,
            'products': []
        }
        for product in vendor.products:
            product_data = {
                'ProductID': product.ProductID,
                'ProductName': product.ProductName,
                'Description': product.Description,
                'ResultsDisplayedInIDS7': product.ResultsDisplayedInIDS7,
                'DICOMOutput': product.DICOMOutput,
                'WorklistIntegration': product.WorklistIntegration,
                'PrePopulatedReports': product.PrePopulatedReports,
                'regulatory_approved_pathologies': []
            }
            for approval in product.approvals:
                pathology = session.query(Pathology).filter_by(PathologyID=approval.PathologyID).first()
                pathology_data = {
                    'id': pathology.PathologyID,
                    'name': pathology.PathologyName,
                    'approval_status': approval.ApprovalStatus,
                    'approval_date': approval.ApprovalDate.isoformat(),
                    'approved_by': approval.ApprovedBy
                }
                product_data['regulatory_approved_pathologies'].append(pathology_data)
            vendor_data['products'].append(product_data)
        return jsonify(vendor_data), 200
    except Exception as e:
        abort(500, description=str(e))


## Update Endpoint API Endpoint
@app.route('/api/vendors/<vendor_id>', methods=['PUT'])
@login_required
def update_vendor_api(vendor_id):
    session = Session
    data = request.get_json()
    try:
        vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
        if not vendor:
            abort(404, description="Vendor not found")
        # Update vendor details API Endpoint
        vendor.VendorName = data.get('VendorName', vendor.VendorName)
        vendor.ContactEmail = data.get('ContactEmail', vendor.ContactEmail)
        vendor.Website = data.get('Website', vendor.Website)
        session.commit()
        return jsonify({"message": "Vendor updated successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))


## Delete Endpoint API Endpoint
@app.route('/api/vendors/<vendor_id>', methods=['DELETE'])
@login_required
def delete_vendor_api(vendor_id):
    session = Session
    try:
        vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
        if not vendor:
            abort(404, description="Vendor not found")
        session.delete(vendor)
        session.commit()
        return jsonify({"message": "Vendor deleted successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## GUI endpoints

## Root GUI endpoint
@app.route('/')
def index_gui():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        session = Session
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Check if the user or email already exists
            existing_user = session.query(User).filter((User.Username == username) | (User.Email == email)).first()
            if existing_user:
                flash('Username or email already exists', 'danger')
                return redirect(url_for('signup'))

            # Create a new user
            user = User(Username=username, Email=email)
            user.set_password(password)
            session.add(user)
            session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
            session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session = Session
        email = request.form['email']
        password = request.form['password']
        user = session.query(User).filter_by(Email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index_gui'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


## Vendors GUI endpoint
@app.route('/vendors')
def list_vendors_gui():
    session = Session
    try:
        vendors = session.query(Vendor).all()
        return render_template('vendors.html', vendors=vendors)
    except Exception as e:
        abort(500, description=str(e))


## Vendor GUI endpoint
@app.route('/vendor/<vendor_id>')
def vendor_detail_gui(vendor_id):
    session = Session
    try:
        vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
        if not vendor:
            abort(404, description="Vendor not found")
        return render_template('vendor_detail.html', vendor=vendor)
    except Exception as e:
        abort(500, description=str(e))


## Add Vendor GUI endpoint
@app.route('/add_vendor', methods=['GET', 'POST'])
@login_required
def add_vendor_gui():
    if request.method == 'POST':
        session = Session
        try:
            vendor_id = request.form['VendorID']
            vendor_name = request.form['VendorName']
            contact_email = request.form['ContactEmail']
            website = request.form['Website']

            vendor = Vendor(
                VendorID=vendor_id,
                VendorName=vendor_name,
                ContactEmail=contact_email,
                Website=website
            )
            session.add(vendor)
            session.commit()
            flash('Vendor added successfully!', 'success')
            return redirect(url_for('list_vendors_gui'))
        except SQLAlchemyError as e:
            session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('add_vendor.html')


## Edit Vendor GUI endpoint
@app.route('/gui/edit_vendor/<vendor_id>', methods=['GET', 'POST'])
@login_required
def edit_vendor_gui(vendor_id):
    session = Session
    try:
        vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
        if not vendor:
            abort(404, description="Vendor not found")
        if request.method == 'POST':
            vendor.VendorName = request.form['VendorName']
            vendor.ContactEmail = request.form['ContactEmail']
            vendor.Website = request.form['Website']
            session.commit()
            flash('Vendor updated successfully!', 'success')
            return redirect(url_for('vendor_detail_gui', vendor_id=vendor.VendorID))
        return render_template('edit_vendor.html', vendor=vendor)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_vendors_gui'))

## Delete Vendor GUI endpoint
@app.route('/delete_vendor/<vendor_id>', methods=['GET', 'POST'])
@login_required
def delete_vendor_gui(vendor_id):
    session = Session
    try:
        vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
        if not vendor:
            abort(404, description="Vendor not found")
        if request.method == 'POST':
            session.delete(vendor)
            session.commit()
            flash('Vendor deleted successfully!', 'success')
            return redirect(url_for('list_vendors_gui'))
        return render_template('delete_vendor.html', vendor=vendor)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_vendors_gui'))
    
## Products
@app.route('/products')
def list_products_gui():
    session = Session
    try:
        products = session.query(Product).all()
        return render_template('products.html', products=products)
    except Exception as e:
        abort(500, description=str(e))

# List products
@app.route('/product/<product_id>')
def product_detail_gui(product_id):
    session = Session
    try:
        product = session.query(Product).filter_by(ProductID=product_id).first()
        if not product:
            abort(404, description="Product not found")
        
        pathologies = session.query(Pathology).all()
        
        return render_template('product_detail.html', product=product, pathologies=pathologies)
    except Exception as e:
        print(traceback.format_exc())
        abort(500, description=str(e))

# Add Products
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product_gui():
    session = Session
    try:
        if request.method == 'POST':
            product_id = request.form['ProductID']
            product_name = request.form['ProductName']
            description = request.form['Description']
            vendor_id = request.form['VendorID']
            results_displayed_in_ids7 = 'ResultsDisplayedInIDS7' in request.form
            dicom_output = request.form['DICOMOutput']
            worklist_integration = 'WorklistIntegration' in request.form
            prepopulated_reports = 'PrePopulatedReports' in request.form

            # Check if vendor exists
            vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
            if not vendor:
                flash('Vendor not found', 'danger')
                return redirect(url_for('add_product_gui'))

            product = Product(
                ProductID=product_id,
                ProductName=product_name,
                Description=description,
                VendorID=vendor_id,
                vendor_=vendor,
                ResultsDisplayedInIDS7=results_displayed_in_ids7,
                DICOMOutput=dicom_output,
                WorklistIntegration=worklist_integration,
                PrePopulatedReports=prepopulated_reports
            )
            session.add(product)
            session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('list_products_gui'))
        else:
            # Get list of vendors for the select field
            vendors = session.query(Vendor).all()
            return render_template('add_product.html', vendors=vendors)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('add_product_gui'))

# Edit product
@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product_gui(product_id):
    session = Session
    try:
        product = session.query(Product).filter_by(ProductID=product_id).first()
        if not product:
            abort(404, description="Product not found")

        if request.method == 'POST':
            product.ProductName = request.form['ProductName']
            product.Description = request.form['Description']
            vendor_id = request.form['VendorID']

            # Check if vendor exists
            vendor = session.query(Vendor).filter_by(VendorID=vendor_id).first()
            if not vendor:
                flash('Vendor not found', 'danger')
                return redirect(url_for('edit_product_gui', product_id=product_id))

            product.VendorID = vendor_id
            product.vendor_ = vendor
            product.ResultsDisplayedInIDS7 = 'ResultsDisplayedInIDS7' in request.form
            product.DICOMOutput = request.form['DICOMOutput']
            product.WorklistIntegration = 'WorklistIntegration' in request.form
            product.PrePopulatedReports = 'PrePopulatedReports' in request.form

            session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('product_detail_gui', product_id=product.ProductID))
        else:
            # Get list of vendors for the select field
            vendors = session.query(Vendor).all()
            return render_template('edit_product.html', product=product, vendors=vendors)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_products_gui'))

# Delete product
@app.route('/delete_product/<product_id>', methods=['GET', 'POST'])
@login_required
def delete_product_gui(product_id):
    session = Session
    try:
        product = session.query(Product).filter_by(ProductID=product_id).first()
        if not product:
            abort(404, description="Product not found")
        if request.method == 'POST':
            session.delete(product)
            session.commit()
            flash('Product deleted successfully!', 'success')
            return redirect(url_for('list_products_gui'))
        return render_template('delete_product.html', product=product)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_products_gui'))

## Regulatory Approvals

@app.route('/add_regulatory_approval/<string:product_id>', methods=['POST'])
@login_required
def add_regulatory_approval(product_id):
    session = Session()
    try:
        pathology_id = request.form['PathologyID']
        approved_by = request.form['ApprovedBy']
        approval_date = request.form['ApprovalDate']

        # Validate inputs
        if not pathology_id or not approved_by or not approval_date:
            flash('Please fill in all fields', 'danger')
            return redirect(url_for('product_detail_gui', product_id=product_id))

        # Check if product exists
        product = session.query(Product).filter_by(ProductID=product_id).first()
        if not product:
            flash('Product not found', 'danger')
            return redirect(url_for('list_products_gui'))

        # Create and add regulatory approval
        new_approval = RegulatoryApproval(
            ProductID=product_id,
            PathologyID=pathology_id,
            ApprovedBy=approved_by,
            ApprovalDate=datetime.strptime(approval_date, '%Y-%m-%d').date()
        )
        session.add(new_approval)
        session.commit()

        flash('Regulatory approval added successfully', 'success')
        return redirect(url_for('product_detail_gui', product_id=product_id))
    except Exception as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('product_detail_gui', product_id=product_id))


@app.route('/remove_regulatory_approval/<string:approval_id>', methods=['POST'])
@login_required
def remove_regulatory_approval(approval_id):
    session = Session()
    try:
        approval = session.query(RegulatoryApproval).filter_by(ApprovalID=approval_id).first()
        if not approval:
            flash('Regulatory approval not found', 'danger')
            return redirect(url_for('list_products_gui'))

        product_id = approval.ProductID
        session.delete(approval)
        session.commit()

        flash('Regulatory approval removed successfully', 'success')
        return redirect(url_for('product_detail_gui', product_id=product_id))
    except Exception as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_products_gui'))