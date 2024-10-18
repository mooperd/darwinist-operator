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


## GUI endpoints

## Vendors GUI endpoint
@app.route('/vendors')
def list_vendors_gui():
    session = Session
    try:
        vendors = session.query(Vendor).all()
        print(vendors)
        return render_template('vendors.html', vendors=vendors)
    except Exception as e:
        abort(500, description=str(e))


## Vendor GUI endpoint
@app.route('/vendor/<vendor_id>')
def vendor_detail_gui(vendor_id):
    session = Session
    try:
        vendor = session.query(Vendor).filter_by(vendor_id=vendor_id).first()
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

def add_product_gui():
    session = Session
    try:
        if request.method == 'POST':
            product_id = request.form['ProductID']
            product_name = request.form['product_name']
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
                product_name=product_name,
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
            product.product_name = request.form['product_name']
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