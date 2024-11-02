from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship, declarative_base, joinedload
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import date, datetime
from model import *
from app import app
import traceback
import markdown

@app.route('/trials')
def list_trials_gui():
    session = Session
    try:
        trials = session.query(ClinicalTrial).options(joinedload(ClinicalTrial.product)).all()
        return render_template('clinical_trial/trails.html', trials=trials)
    except Exception as e:
        traceback.print_exc()
        abort(500, description=str(e))


@app.route('/trial/<int:trial_id>')
def trial_detail_gui(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).options(
            joinedload(ClinicalTrial.product),
            joinedload(ClinicalTrial.enrollments).joinedload(TrialEnrollment.patient)
        ).filter_by(trial_id=trial_id).first()
        patients = session.query(Patient).all()
        if not trial:
            abort(404, description="Clinical trial not found")
        return render_template('clinical_trial/trial_detail.html', trial=trial, patients=patients)
    except Exception as e:
        abort(500, description=str(e))


@app.route('/add_trial', methods=['GET', 'POST'])
def add_trial_gui():
    session = Session
    try:
        if request.method == 'POST':
            trial_name = request.form['TrialName']
            description = request.form['Description']
            start_date = request.form['StartDate']
            end_date = request.form.get('EndDate')
            trial_type = request.form['TrialType']
            product_id = request.form['ProductID']

            # Validate required fields
            if not trial_name or not start_date or not trial_type or not product_id:
                flash('Please fill in all required fields', 'danger')
                return redirect(url_for('add_trial_gui'))

            # Check if product exists
            product = session.query(Product).filter_by(product_id=product_id).first()
            if not product:
                flash('Product not found', 'danger')
                return redirect(url_for('add_trial_gui'))

            # Parse dates
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

            trial = ClinicalTrial(
                trial_name=trial_name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                trial_type=trial_type,
                product=product
            )
            session.add(trial)
            session.commit()
            flash('Clinical trial added successfully!', 'success')
            return redirect(url_for('list_trials_gui'))
        else:
            products = session.query(Product).all()
            return render_template('clinical_trial/add_trial.html', products=products)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('add_trial_gui'))

@app.route('/edit_trial/<int:trial_id>', methods=['GET', 'POST'])
def edit_trial_gui(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).filter_by(trial_id=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        if request.method == 'POST':
            trial.trail_name = request.form['trail_name']
            trial.description = request.form['description']
            trial_type = request.form['TrialType']
            start_date = request.form['StartDate']
            end_date = request.form.get('EndDate')
            product_id = request.form['ProductID']

            # Validate required fields
            if not trial.trail_name or not start_date or not trial_type or not product_id:
                flash('Please fill in all required fields', 'danger')
                return redirect(url_for('edit_trial_gui', trial_id=trial_id))

            # Check if product exists
            product = session.query(Product).filter_by(ProductID=product_id).first()
            if not product:
                flash('Product not found', 'danger')
                return redirect(url_for('edit_trial_gui', trial_id=trial_id))

            # Parse dates
            trial.StartDate = datetime.strptime(start_date, '%Y-%m-%d').date()
            trial.EndDate = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            trial.TrialType = trial_type
            trial.product = product

            session.commit()
            flash('Clinical trial updated successfully!', 'success')
            return redirect(url_for('trial_detail_gui', trial_id=trial.trial_id))
        else:
            products = session.query(Product).all()
            return render_template('clinical_trial/edit_trial.html', trial=trial, products=products)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_trials_gui'))

@app.route('/delete_trial/<int:trial_id>', methods=['GET', 'POST'])
def delete_trial_gui(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).filter_by(trial_id=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")
        if request.method == 'POST':
            session.delete(trial)
            session.commit()
            flash('Clinical trial deleted successfully!', 'success')
            return redirect(url_for('list_trials_gui'))
        return render_template('clinical_trial/delete_trial.html', trial=trial)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_trials_gui'))

# Trial Patient GUI

@app.route('/patients')
def list_patients_gui():
    session = Session
    try:
        patients = session.query(Patient).all()
        return render_template('clinical_trial/patients.html', patients=patients)
    except Exception as e:
        abort(500, description=str(e))

@app.route('/patient/<int:patient_id>')
def patient_detail_gui(patient_id):
    session = Session
    try:
        patient = session.query(Patient).options(
            joinedload(Patient.enrollments).joinedload(TrialEnrollment.trial)
        ).filter_by(patient_id=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")
        # Convert medical_history from Markdown to HTML
        patient.medical_history = markdown.markdown(patient.medical_history)
        return render_template('clinical_trial/patient_detail.html', patient=patient)
    except Exception as e:
        abort(500, description=str(e))

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient_gui():
    session = Session
    try:
        if request.method == 'POST':
            name = request.form['Name']
            age = request.form['Age']
            gender = request.form['Gender']
            medical_history = request.form['medical_history']

            if not name or not gender:
                flash('Name and Gender are required', 'danger')
                return redirect(url_for('add_patient_gui'))

            patient = Patient(
                name=name,
                age=age if age else None,
                gender=gender,
                medical_history=medical_history
            )
            session.add(patient)
            session.commit()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('list_patients_gui'))
        else:
            return render_template('clinical_trial/add_patient.html')
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('add_patient_gui'))

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient_gui(patient_id):
    session = Session
    try:
        patient = session.query(Patient).filter_by(patient_id=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")

        if request.method == 'POST':
            patient.name = request.form['Name']
            patient.age = request.form['Age'] if request.form['Age'] else None
            patient.gender = request.form['Gender']
            patient.medical_history = request.form['medical_history']

            if not patient.name or not patient.gender:
                flash('Name and Gender are required', 'danger')
                return redirect(url_for('edit_patient_gui', patient_id=patient_id))

            session.commit()
            flash('Patient updated successfully!', 'success')
            return redirect(url_for('patient_detail_gui', patient_id=patient.patient_id))
        else:
            return render_template('clinical_trial/edit_patient.html', patient=patient)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_patients_gui'))
    
@app.route('/delete_patient/<int:patient_id>', methods=['GET', 'POST'])
def delete_patient_gui(patient_id):
    session = Session
    try:
        patient = session.query(Patient).filter_by(patient_id=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")
        if request.method == 'POST':
            session.delete(patient)
            session.commit()
            flash('Patient deleted successfully!', 'success')
            return redirect(url_for('list_patients_gui'))
        return render_template('clinical_trial/delete_patient.html', patient=patient)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('list_patients_gui'))




# Enrollments

@app.route('/trial/<int:trial_id>/enroll', methods=['GET', 'POST'])
def enroll_patient_gui(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).filter_by(trial_id=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        if request.method == 'POST':
            patient_id = request.form['patient_id']

            # Check if patient exists
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            if not patient:
                flash('Patient not found', 'danger')
                return redirect(url_for('enroll_patient_gui', trial_id=trial_id))

            # Check if patient is already enrolled
            existing_enrollment = session.query(TrialEnrollment).filter_by(
                trial_id=trial_id, patient_id=patient_id).first()
            if existing_enrollment:
                flash('Patient is already enrolled in this trial', 'danger')
                return redirect(url_for('enroll_patient_gui', trial_id=trial_id))

            enrollment = TrialEnrollment(
                trial_id=trial_id,
                patient_id=patient_id,
                date_enrolled=date.today()
            )
            session.add(enrollment)
            session.commit()
            flash('Patient enrolled successfully!', 'success')
            return redirect(url_for('trial_detail_gui', trial_id=trial_id))
        else:
            patients = session.query(Patient).all()
            return render_template('clinical_trial/enroll_patient.html', trial=trial, patients=patients)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('trial_detail_gui', trial_id=trial_id))



@app.route('/enrollment/<int:enrollment_id>/add_result', methods=['GET', 'POST'])
def add_trial_result_gui(enrollment_id):
    session = Session
    try:
        enrollment = session.query(TrialEnrollment).options(
            joinedload(TrialEnrollment.patient),
            joinedload(TrialEnrollment.trial)
        ).filter_by(EnrollmentID=enrollment_id).first()
        if not enrollment:
            abort(404, description="Enrollment not found")

        if request.method == 'POST':
            outcome = request.form['Outcome']
            additional_data = request.form['AdditionalData']

            if not outcome:
                flash('Outcome is required', 'danger')
                return redirect(url_for('add_trial_result_gui', enrollment_id=enrollment_id))

            result = TrialResult(
                EnrollmentID=enrollment_id,
                Outcome=outcome,
                DateOfResult=date.today(),
                AdditionalData=additional_data
            )
            session.add(result)
            session.commit()
            flash('Trial result recorded successfully!', 'success')
            return redirect(url_for('trial_detail_gui', trial_id=enrollment.trial_id))
        else:
            return render_template('clinical_trial/add_trial_result.html', enrollment=enrollment)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('trial_detail_gui', trial_id=enrollment.trial_id))


