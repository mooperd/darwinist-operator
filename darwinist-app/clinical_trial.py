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
        ).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")
        return render_template('clinical_trial/trial_detail.html', trial=trial)
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
            product = session.query(Product).filter_by(ProductID=product_id).first()
            if not product:
                flash('Product not found', 'danger')
                return redirect(url_for('add_trial_gui'))

            # Parse dates
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

            trial = ClinicalTrial(
                TrialName=trial_name,
                Description=description,
                StartDate=start_date,
                EndDate=end_date,
                TrialType=trial_type,
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
        trial = session.query(ClinicalTrial).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        if request.method == 'POST':
            trial.TrialName = request.form['TrialName']
            trial.Description = request.form['Description']
            trial_type = request.form['TrialType']
            start_date = request.form['StartDate']
            end_date = request.form.get('EndDate')
            product_id = request.form['ProductID']

            # Validate required fields
            if not trial.TrialName or not start_date or not trial_type or not product_id:
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
            return redirect(url_for('trial_detail_gui', trial_id=trial.TrialID))
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
        trial = session.query(ClinicalTrial).filter_by(TrialID=trial_id).first()
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
        ).filter_by(PatientID=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")
        # Convert MedicalHistory from Markdown to HTML
        patient.MedicalHistory = markdown.markdown(patient.MedicalHistory)
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
            medical_history = request.form['MedicalHistory']

            if not name or not gender:
                flash('Name and Gender are required', 'danger')
                return redirect(url_for('add_patient_gui'))

            patient = Patient(
                Name=name,
                Age=age if age else None,
                Gender=gender,
                MedicalHistory=medical_history
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
        patient = session.query(Patient).filter_by(PatientID=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")

        if request.method == 'POST':
            patient.Name = request.form['Name']
            patient.Age = request.form['Age'] if request.form['Age'] else None
            patient.Gender = request.form['Gender']
            patient.MedicalHistory = request.form['MedicalHistory']

            if not patient.Name or not patient.Gender:
                flash('Name and Gender are required', 'danger')
                return redirect(url_for('edit_patient_gui', patient_id=patient_id))

            session.commit()
            flash('Patient updated successfully!', 'success')
            return redirect(url_for('patient_detail_gui', patient_id=patient.PatientID))
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
        patient = session.query(Patient).filter_by(PatientID=patient_id).first()
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

# Enrolment

## API

## Create a Clinical Trial
@app.route('/api/trials', methods=['POST'])
def create_clinical_trial_api():
    session = Session
    data = request.get_json()
    try:
        trial_name = data.get('TrialName')
        description = data.get('Description')
        start_date = data.get('StartDate')
        end_date = data.get('EndDate')
        trial_type = data.get('TrialType')
        product_id = data.get('ProductID')

        if not trial_name or not start_date or not trial_type or not product_id:
            abort(400, description="Missing required fields")

        # Check if product exists
        product = session.query(Product).filter_by(ProductID=product_id).first()
        if not product:
            abort(404, description="Product not found")

        # Parse dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

        trial = ClinicalTrial(
            TrialName=trial_name,
            Description=description,
            StartDate=start_date,
            EndDate=end_date,
            TrialType=trial_type,
            product=product
        )
        session.add(trial)
        session.commit()
        return jsonify({"message": "Clinical trial created successfully", "TrialID": trial.TrialID}), 201
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Get a Specific Clinical Trial
@app.route('/api/trials/<int:trial_id>', methods=['GET'])
def get_clinical_trial_api(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).options(
            joinedload(ClinicalTrial.product),
            joinedload(ClinicalTrial.enrollments).joinedload(TrialEnrollment.patient)
        ).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        trial_data = {
            "TrialID": trial.TrialID,
            "TrialName": trial.TrialName,
            "Description": trial.Description,
            "StartDate": trial.StartDate.isoformat(),
            "EndDate": trial.EndDate.isoformat() if trial.EndDate else None,
            "TrialType": trial.TrialType,
            "Product": {
                "ProductID": trial.product.ProductID,
                "ProductName": trial.product.ProductName
            },
            "Enrollments": [
                {
                    "EnrollmentID": enrollment.EnrollmentID,
                    "Patient": {
                        "PatientID": enrollment.patient.PatientID,
                        "Name": enrollment.patient.Name
                    },
                    "DateEnrolled": enrollment.DateEnrolled.isoformat()
                } for enrollment in trial.enrollments
            ]
        }
        return jsonify(trial_data), 200
    except Exception as e:
        abort(500, description=str(e))

## Update a Clinical Trial
@app.route('/api/trials/<int:trial_id>', methods=['PUT'])
def update_clinical_trial_api(trial_id):
    session = Session
    data = request.get_json()
    try:
        trial = session.query(ClinicalTrial).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        trial.TrialName = data.get('TrialName', trial.TrialName)
        trial.Description = data.get('Description', trial.Description)
        trial_type = data.get('TrialType')
        if trial_type:
            trial.TrialType = trial_type
        start_date = data.get('StartDate')
        if start_date:
            trial.StartDate = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = data.get('EndDate')
        if end_date:
            trial.EndDate = datetime.strptime(end_date, '%Y-%m-%d').date()

        session.commit()
        return jsonify({"message": "Clinical trial updated successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Delete a Clinical Trial
@app.route('/api/trials/<int:trial_id>', methods=['DELETE'])
def delete_clinical_trial_api(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")
        session.delete(trial)
        session.commit()
        return jsonify({"message": "Clinical trial deleted successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))


# Enrollments

@app.route('/trial/<int:trial_id>/enroll', methods=['GET', 'POST'])
def enroll_patient_gui(trial_id):
    session = Session
    try:
        trial = session.query(ClinicalTrial).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        if request.method == 'POST':
            patient_id = request.form['PatientID']

            # Check if patient exists
            patient = session.query(Patient).filter_by(PatientID=patient_id).first()
            if not patient:
                flash('Patient not found', 'danger')
                return redirect(url_for('enroll_patient_gui', trial_id=trial_id))

            # Check if patient is already enrolled
            existing_enrollment = session.query(TrialEnrollment).filter_by(
                TrialID=trial_id, PatientID=patient_id).first()
            if existing_enrollment:
                flash('Patient is already enrolled in this trial', 'danger')
                return redirect(url_for('enroll_patient_gui', trial_id=trial_id))

            enrollment = TrialEnrollment(
                TrialID=trial_id,
                PatientID=patient_id,
                DateEnrolled=date.today()
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
            return redirect(url_for('trial_detail_gui', trial_id=enrollment.TrialID))
        else:
            return render_template('clinical_trial/add_trial_result.html', enrollment=enrollment)
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('trial_detail_gui', trial_id=enrollment.TrialID))


## Patients API Endpoints

## Create a Patient
@app.route('/api/patients', methods=['POST'])
def create_patient_api():
    session = Session
    data = request.get_json()
    try:
        name = data.get('Name')
        age = data.get('Age')
        gender = data.get('Gender')
        medical_history = data.get('MedicalHistory')

        if not name or not gender:
            abort(400, description="Missing required fields")

        patient = Patient(
            Name=name,
            Age=age,
            Gender=gender,
            MedicalHistory=medical_history
        )
        session.add(patient)
        session.commit()
        return jsonify({"message": "Patient created successfully", "PatientID": patient.PatientID}), 201
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Get All Patients
@app.route('/api/patients', methods=['GET'])
def get_patients_api():
    session = Session
    try:
        patients = session.query(Patient).all()
        result = [
            {
                "PatientID": patient.PatientID,
                "Name": patient.Name,
                "Age": patient.Age,
                "Gender": patient.Gender,
                "MedicalHistory": patient.MedicalHistory
            } for patient in patients
        ]
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=str(e))

## Get a Specific Patient
@app.route('/api/patients/<int:patient_id>', methods=['GET'])
def get_patient_api(patient_id):
    session = Session
    try:
        patient = session.query(Patient).options(
            joinedload(Patient.enrollments).joinedload(TrialEnrollment.trial)
        ).filter_by(PatientID=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")
        patient_data = {
            "PatientID": patient.PatientID,
            "Name": patient.Name,
            "Age": patient.Age,
            "Gender": patient.Gender,
            "MedicalHistory": patient.MedicalHistory,
            "Enrollments": [
                {
                    "EnrollmentID": enrollment.EnrollmentID,
                    "Trial": {
                        "TrialID": enrollment.trial.TrialID,
                        "TrialName": enrollment.trial.TrialName
                    },
                    "DateEnrolled": enrollment.DateEnrolled.isoformat()
                } for enrollment in patient.enrollments
            ]
        }
        return jsonify(patient_data), 200
    except Exception as e:
        abort(500, description=str(e))

## Update a Patient
@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient_api(patient_id):
    session = Session
    data = request.get_json()
    try:
        patient = session.query(Patient).filter_by(PatientID=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")

        patient.Name = data.get('Name', patient.Name)
        patient.Age = data.get('Age', patient.Age)
        patient.Gender = data.get('Gender', patient.Gender)
        patient.MedicalHistory = data.get('MedicalHistory', patient.MedicalHistory)

        session.commit()
        return jsonify({"message": "Patient updated successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Delete a Patient
@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient_api(patient_id):
    session = Session
    try:
        patient = session.query(Patient).filter_by(PatientID=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")
        session.delete(patient)
        session.commit()
        return jsonify({"message": "Patient deleted successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Trial Enrollments API Endpoints

## Enroll a Patient in a Trial
@app.route('/api/trials/<int:trial_id>/enroll', methods=['POST'])
def enroll_patient_api(trial_id):
    session = Session
    data = request.get_json()
    try:
        patient_id = data.get('PatientID')
        if not patient_id:
            abort(400, description="PatientID is required")

        # Check if trial exists
        trial = session.query(ClinicalTrial).filter_by(TrialID=trial_id).first()
        if not trial:
            abort(404, description="Clinical trial not found")

        # Check if patient exists
        patient = session.query(Patient).filter_by(PatientID=patient_id).first()
        if not patient:
            abort(404, description="Patient not found")

        # Check if patient is already enrolled in the trial
        existing_enrollment = session.query(TrialEnrollment).filter_by(
            TrialID=trial_id, PatientID=patient_id).first()
        if existing_enrollment:
            abort(400, description="Patient is already enrolled in this trial")

        enrollment = TrialEnrollment(
            TrialID=trial_id,
            PatientID=patient_id,
            DateEnrolled=date.today()
        )
        session.add(enrollment)
        session.commit()
        return jsonify({"message": "Patient enrolled successfully", "EnrollmentID": enrollment.EnrollmentID}), 201
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Get All Enrollments for a Trial
@app.route('/api/trials/<int:trial_id>/enrollments', methods=['GET'])
def get_trial_enrollments_api(trial_id):
    session = Session
    try:
        enrollments = session.query(TrialEnrollment).options(
            joinedload(TrialEnrollment.patient)
        ).filter_by(TrialID=trial_id).all()
        result = [
            {
                "EnrollmentID": enrollment.EnrollmentID,
                "Patient": {
                    "PatientID": enrollment.patient.PatientID,
                    "Name": enrollment.patient.Name
                },
                "DateEnrolled": enrollment.DateEnrolled.isoformat()
            } for enrollment in enrollments
        ]
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=str(e))

## Get All Enrollments for a Patient
@app.route('/api/patients/<int:patient_id>/enrollments', methods=['GET'])
def get_patient_enrollments_api(patient_id):
    session = Session
    try:
        enrollments = session.query(TrialEnrollment).options(
            joinedload(TrialEnrollment.trial)
        ).filter_by(PatientID=patient_id).all()
        result = [
            {
                "EnrollmentID": enrollment.EnrollmentID,
                "Trial": {
                    "TrialID": enrollment.trial.TrialID,
                    "TrialName": enrollment.trial.TrialName
                },
                "DateEnrolled": enrollment.DateEnrolled.isoformat()
            } for enrollment in enrollments
        ]
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=str(e))

## Trial Results API Endpoints

## Record a Trial Result
@app.route('/api/enrollments/<int:enrollment_id>/results', methods=['POST'])
@login_required
def record_trial_result_api(enrollment_id):
    session = Session
    data = request.get_json()
    try:
        outcome = data.get('Outcome')
        additional_data = data.get('AdditionalData')

        if not outcome:
            abort(400, description="Outcome is required")

        # Check if enrollment exists
        enrollment = session.query(TrialEnrollment).filter_by(EnrollmentID=enrollment_id).first()
        if not enrollment:
            abort(404, description="Enrollment not found")

        result = TrialResult(
            EnrollmentID=enrollment_id,
            Outcome=outcome,
            DateOfResult=date.today(),
            AdditionalData=additional_data
        )
        session.add(result)
        session.commit()
        return jsonify({"message": "Trial result recorded successfully", "ResultID": result.ResultID}), 201
    except SQLAlchemyError as e:
        session.rollback()
        abort(500, description=str(e))

## Get All Results for a Trial
@app.route('/api/trials/<int:trial_id>/results', methods=['GET'])
def get_trial_results_api(trial_id):
    session = Session
    try:
        results = session.query(TrialResult).join(TrialEnrollment).filter(
            TrialEnrollment.TrialID == trial_id).options(
            joinedload(TrialResult.enrollment).joinedload(TrialEnrollment.patient)
        ).all()
        result_data = [
            {
                "ResultID": result.ResultID,
                "EnrollmentID": result.EnrollmentID,
                "Patient": {
                    "PatientID": result.enrollment.patient.PatientID,
                    "Name": result.enrollment.patient.Name
                },
                "Outcome": result.Outcome,
                "DateOfResult": result.DateOfResult.isoformat(),
                "AdditionalData": result.AdditionalData
            } for result in results
        ]
        return jsonify(result_data), 200
    except Exception as e:
        abort(500, description=str(e))