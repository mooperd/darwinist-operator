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


## Approval GUI endpoints
@app.route('/approvals')
def index():
    session = Session()
    approvals = session.query(Approval).all()
    return render_template('approval/approval.html', approvals=approvals)


@app.route('/approvals/new', methods=['GET', 'POST'])
def approvals():
    session = Session()
    
    # Handle form submission
    if request.method == 'POST':
        try:
            # Retrieve data from the form
            approval_date = request.form['approval_date']
            approval_status = True if request.form.get('approval_status') == 'on' else False
            id_code = request.form['id_code']
            product_id = request.form['product_id']
            pathology_id = request.form['pathology_id']
            modality_id = request.form['modality_id']
            body_part_id = request.form['body_part_id']
            regulatory_body_id = request.form['regulatory_body_id']

            # Create a new Approval object
            new_approval = Approval(
                approval_date=approval_date,
                approval_status=approval_status,
                id_code=id_code,
                product_id=product_id,
                pathology_id=pathology_id,
                modality_id=modality_id,
                body_part_id=body_part_id,
                regulatory_body_id=regulatory_body_id
            )
            
            # Add to the session and commit
            session.add(new_approval)
            session.commit()

            flash("New approval has been created successfully!", "success")
            return redirect(url_for('index'))
        
        except Exception as e:
            session.rollback()
            flash(f"Error creating approval: {str(e)}", "danger")
            return redirect(url_for('approvals'))
    
    # For GET request, render the form
    products = session.query(Product).all()
    pathologies = session.query(Pathology).all()
    modalities = session.query(Modality).all()
    body_parts = session.query(BodyPart).all()
    regulatory_bodies = session.query(RegulatoryBody).all()

    return render_template(
        'approval/new_approval.html',
        products=products,
        pathologies=pathologies,
        modalities=modalities,
        body_parts=body_parts,
        regulatory_bodies=regulatory_bodies
    )