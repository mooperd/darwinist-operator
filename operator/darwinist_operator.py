import kopf
import kubernetes.client
from kubernetes.client.rest import ApiException
import os

# Load Kubernetes configuration
kubernetes.config.load_incluster_config()  # Use this if running inside a cluster
# kubernetes.config.load_kube_config()     # Use this if running locally for testing

@kopf.on.create('imageprocessingjobs')
def on_create(spec, name, namespace, logger, patch, **kwargs):
    #TODO: Fix hardcoded namespace here!
    namespace="darwinist"
    logger.info(f"Processing ImageProcessingJob {name} in namespace {namespace}")

    s3_input_location = spec.get('s3_input_location')
    model_name = spec.get('model_name')
    s3_output_location = spec.get('s3_output_location')

    # Validate input
    if not s3_input_location or not model_name or not s3_output_location:
        raise kopf.HandledException("Missing required spec fields.")

    # Define the job name
    job_name = f"ipj-{name}"

    # Define the container image to use (replace with your actual image)
    container_image = "nvcr.io/nvidia/cloud-native/dcgm:3.3.0-1-ubuntu22.04"

    # Define the Kubernetes Job
    job_manifest = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': job_name,
            'namespace': namespace,
            'ownerReferences': [
                {
                    'apiVersion': 'darwinist.io/v1',
                    'kind': 'ImageProcessingJob',
                    'name': name,
                    'uid': kwargs['body']['metadata']['uid'],
                }
            ],
        },
        'spec': {
            'template': {
                'metadata': {
                    'labels': {
                        'job-name': job_name
                    }
                },
                'spec': {
                    'containers': [
                        {
                            'name': 'image-processor',
                            'image': container_image,
                            'command': ["/usr/bin/dcgmproftester12"],
                            'args': ["--no-dcgm-validation", "-t 1004", "-d 30"],
                            'resources': {'limits': {"nvidia.com/gpu": 1}},
                            'env': [
                                {'name': 'S3_INPUT_LOCATION', 'value': s3_input_location},
                                {'name': 'MODEL_NAME', 'value': model_name},
                                {'name': 'S3_OUTPUT_LOCATION', 'value': s3_output_location},
                            ],
                            # Add any other necessary configurations (e.g., volume mounts)
                        }
                    ],
                    'restartPolicy': 'Never',
                }
            },
            'backoffLimit': 3,
        }
    }

    # Create the Job
    batch_v1 = kubernetes.client.BatchV1Api()
    try:
        batch_v1.create_namespaced_job(namespace=namespace, body=job_manifest)
        logger.info(f"Job {job_name} created successfully.")
        # Update the status to reflect that the job is created
        patch.status['state'] = 'Created'
        patch.status['message'] = f'Job {job_name} created and running.'
    except ApiException as e:
        logger.error(f"Exception when creating Job: {e}")
        raise kopf.TemporaryError(f"Failed to create Job {job_name}", delay=30)

@kopf.on.delete('imageprocessingjobs')
def on_delete(spec, name, namespace, logger, **kwargs):
    logger.info(f"Cleaning up resources for ImageProcessingJob {name}")
    job_name = f"ipj-{name}"

    # Delete the Job
    batch_v1 = kubernetes.client.BatchV1Api()
    try:
        batch_v1.delete_namespaced_job(
            name=job_name,
            namespace=namespace,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground'
            )
        )
        logger.info(f"Job {job_name} deleted.")
    except ApiException as e:
        logger.error(f"Exception when deleting Job: {e}")