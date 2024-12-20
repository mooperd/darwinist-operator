from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.orm import joinedload
from model import *
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from kubernetes import client, config
from model import *
from app import app
from utilities import get_image_processing_details
import uuid
import os

# Load Kubernetes configuration
# config.load_incluster_config()  # Use this if running inside a cluster
config.load_kube_config()     # Use this if running locally for testing


# Define Flask-WTF form
class ImageProcessingForm(FlaskForm):
    s3_input_location = StringField('S3 Input Location', validators=[DataRequired(), URL()])
    model_name = StringField('Model Name', validators=[DataRequired()])
    s3_output_location = StringField('S3 Output Location', validators=[DataRequired(), URL()])
    submit = SubmitField('Submit')

@app.route("/submit_job", methods=['GET', 'POST'])
def submit_job():
    form = ImageProcessingForm()
    # if form.validate_on_submit():
    if request.method == 'POST':
        s3_input_location = form.s3_input_location.data
        model_name = form.model_name.data
        s3_output_location = form.s3_output_location.data

        api_instance = client.CustomObjectsApi()
        group = 'darwinist.io'
        version = 'v1'
        namespace = 'darwinist'  # Change if needed
        plural = 'imageprocessingjobs'

        # Generate a unique name for the custom resource
        resource_name = f"ipj-{uuid.uuid4().hex[:6]}"

        body = {
            'apiVersion': f'{group}/{version}',
            'kind': 'ImageProcessingJob',
            'metadata': {
                'name': resource_name,
            },
            'spec': {
                's3_input_location': s3_input_location,
                'model_name': model_name,
                's3_output_location': s3_output_location,
            }
        }

        try:
            api_instance.create_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                body=body,
            )
            flash(f'Image processing job "{resource_name}" created successfully.', 'success')
            return redirect(url_for('submit_job'))
        except client.rest.ApiException as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('jobs/submit_job.html', form=form)


@app.route('/trial/<int:trial_id>/launch_jobs', methods=['POST'])
def launch_image_processing_jobs(trial_id):
    session = Session()
    try:
        trial = session.query(ClinicalTrial).options(
            joinedload(ClinicalTrial.product),
            joinedload(ClinicalTrial.enrollments).joinedload(TrialEnrollment.patient)
        ).filter_by(trial_id=trial_id).first()

        if not trial:
            abort(404, description="Clinical trial not found")

        if not trial.enrollments:
            flash('No patients enrolled in this trial.', 'warning')
            return redirect(url_for('trial_detail_gui', trial_id=trial_id))

        api_instance = client.CustomObjectsApi()
        group = 'darwinist.io'
        version = 'v1'
        namespace = 'darwinist'  # Change if needed
        plural = 'imageprocessingjobs'

        for enrollment in trial.enrollments:
            if enrollment.image_processing_job_id:
                # Job already exists for this enrollment
                continue

            patient_id = enrollment.patient_id
            patient = enrollment.patient

            # Prepare job details
            s3_input_location = f"s3://input-data/patient-{patient_id}"
            model_name = trial.product.product_name  # Assuming model_name is the product name
            s3_output_location = f"s3://output-data/trial-{trial_id}/patient-{patient_id}"

            # Generate a unique name for the ImageProcessingJob
            resource_name = f"ipj-{uuid.uuid4().hex[:6]}"

            body = {
                'apiVersion': f'{group}/{version}',
                'kind': 'ImageProcessingJob',
                'metadata': {
                    'name': resource_name,
                },
                'spec': {
                    's3_input_location': s3_input_location,
                    'model_name': model_name,
                    's3_output_location': s3_output_location,
                }
            }

            try:
                # Create the ImageProcessingJob in Kubernetes
                api_instance.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=body,
                )
                # Store the job ID in the enrollment
                enrollment.image_processing_job_id = resource_name
                session.commit()
            except client.rest.ApiException as e:
                session.rollback()
                flash(f'Error creating ImageProcessingJob for patient {patient.name}: {e.reason}', 'danger')
                return redirect(url_for('trial_detail_gui', trial_id=trial_id))

        flash('Image Processing Jobs launched successfully for all enrolled patients.', 'success')
        return redirect(url_for('trial_detail_gui', trial_id=trial_id))

    except Exception as e:
        session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('trial_detail_gui', trial_id=trial_id))
    finally:
        session.close()



@app.route("/list_jobs", methods=['GET'])
def list_jobs():
    form = ImageProcessingForm()
    api_instance = client.CustomObjectsApi()
    group = 'darwinist.io'
    version = 'v1'
    namespace = 'darwinist'  # Change this if necessary
    plural = 'imageprocessingjobs'
    session = Session()

    try:
        # Get the list of ImageProcessingJob resources from Kubernetes
        jobs = api_instance.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
        )
        job_list = jobs.get('items', [])
        
        # Dictionary to store job-clinical trial and patient associations
        job_trial_mapping = {}
        
        # Loop through each job and retrieve associated clinical trial and patient
        for job in job_list:
            job_id = job['metadata']['name']

            # Query the TrialEnrollment to find the entry with this image_processing_job_id
            enrollment = session.query(TrialEnrollment).filter_by(image_processing_job_id=job_id).first()
            
            if enrollment and enrollment.trial:
                # Get the trial and patient information
                trial_name = enrollment.trial.trial_name
                trial_id = enrollment.trial.trial_id
                patient_name = enrollment.patient.name
                patient_id = enrollment.patient.patient_id

                # Map job name to trial name, patient name, and trial id
                job_trial_mapping[job_id] = {
                    'trial_name': trial_name,
                    'trial_id': trial_id,
                    'patient_name': patient_name,
                    'patient_id': patient_id
                }
            else:
                job_trial_mapping[job_id] = {
                    'trial_name': 'N/A',
                    'trial_id': None,
                    'patient_name': 'N/A',
                    'patient_id': None
                }

        return render_template('jobs/list_jobs.html', jobs=job_list, form=form, job_trial_mapping=job_trial_mapping)
    except client.rest.ApiException as e:
        flash(f'Error retrieving jobs: {str(e)}', 'danger')
        return redirect(url_for('jobs/list_jobs.html'))
    finally:
        session.close()


"""
@app.route("/list_jobs", methods=['GET'])
def list_jobs():
    form = ImageProcessingForm()
    api_instance = client.CustomObjectsApi()
    group = 'darwinist.io'
    version = 'v1'
    namespace = 'darwinist'  # Change this if necessary
    plural = 'imageprocessingjobs'

    try:
        # Get the list of ImageProcessingJob resources
        jobs = api_instance.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
        )
        job_list = jobs.get('items', [])
        print(job_list)
        return render_template('jobs/list_jobs.html', jobs=job_list, form=form)
    except client.rest.ApiException as e:
        flash(f'Error retrieving jobs: {str(e)}', 'danger')
        return redirect(url_for('index'))
"""


@app.route("/job/<name>", methods=['GET'])
def job_detail(name):
    api_instance = client.CustomObjectsApi()
    batch_v1 = client.BatchV1Api()
    core_v1 = client.CoreV1Api()
    group = 'darwinist.io'
    version = 'v1'
    namespace = 'darwinist'  # Change this if necessary
    plural = 'imageprocessingjobs'

    try:
        # Get the specific ImageProcessingJob resource
        job = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=name
        )

        # Get the associated Kubernetes Job
        k8s_job_name = f"ipj-{name}"
        k8s_job = batch_v1.read_namespaced_job(name=k8s_job_name, namespace=namespace)

        # Get the Pods associated with the Kubernetes Job
        pods = core_v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"job-name={k8s_job_name}"
        ).items

        return render_template('jobs/job_detail.html', job=job, k8s_job=k8s_job, pods=pods)
    except client.rest.ApiException as e:
        flash(f'Error retrieving job details: {str(e)}', 'danger')
        return redirect(url_for('list_jobs'))


@app.route("/delete_jobs", methods=['POST'])
def delete_jobs():
    form = ImageProcessingForm()
    selected_job_names = request.form.getlist('job_names')
    if not selected_job_names:
        flash('No jobs selected for deletion.', 'warning')
        return redirect(url_for('list_jobs'))

    api_instance = client.CustomObjectsApi()
    group = 'darwinist.io'
    version = 'v1'
    namespace = 'darwinist'
    plural = 'imageprocessingjobs'

    deleted_jobs = []
    errors = []

    for job_name in selected_job_names:
        try:
            api_instance.delete_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=job_name,
                body=client.V1DeleteOptions()
            )
            deleted_jobs.append(job_name)
        except client.rest.ApiException as e:
            errors.append(f'Error deleting job {job_name}: {str(e)}')

    if deleted_jobs:
        flash(f'Successfully deleted jobs: {", ".join(deleted_jobs)}', 'success')
    if errors:
        flash('\n'.join(errors), 'danger')

    return redirect(url_for('list_jobs'))


@app.route("/pod/<namespace>/<pod_name>/logs", methods=['GET'])
def view_pod_logs(namespace, pod_name):
    core_v1 = client.CoreV1Api()

    try:
        # Fetch the logs of the pod
        logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)
    except ApiException as e:
        flash(f'Error retrieving logs for pod {pod_name}: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('list_jobs'))

    return render_template('jobs/pod_logs.html', pod_name=pod_name, namespace=namespace, logs=logs)


from flask import jsonify

@app.route("/api/trial/<int:trial_id>/job_statuses", methods=['GET'])
def job_statuses(trial_id):
    trial = Session.query(ClinicalTrial).get(trial_id)
    job_statuses = {}
    
    for enrollment in trial.enrollments:
        if enrollment.image_processing_job_id:
            job_details = get_image_processing_details(enrollment.image_processing_job_id)
            job_statuses[enrollment.image_processing_job_id] = {
                'error': job_details.get('error'),
                'pods': [
                    {
                        'name': pod.metadata.name,
                        'phase': pod.status.phase
                    }
                    for pod in job_details.get('k8s_job', {}).get('pods', [])
                ]
            }
    
    return jsonify(job_statuses)

