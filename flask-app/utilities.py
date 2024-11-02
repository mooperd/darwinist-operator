from kubernetes import client

def get_job_status(job_id):
    api_instance = client.CustomObjectsApi()
    group = 'darwinist.io'
    version = 'v1'
    namespace = 'darwinist'
    plural = 'imageprocessingjobs'

    try:
        job = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=job_id
        )
        return job.get('status', {})
    except client.rest.ApiException as e:
        return {'state': 'Unknown', 'message': str(e)}
    

def get_image_processing_details(name):
    api_instance = client.CustomObjectsApi()
    batch_v1 = client.BatchV1Api()
    core_v1 = client.CoreV1Api()
    group = 'darwinist.io'
    version = 'v1'
    namespace = 'darwinist'
    plural = 'imageprocessingjobs'
    
    try:
        # Retrieve the ImageProcessingJob custom resource
        ipj = api_instance.get_namespaced_custom_object(
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

        # Structure the information with Kubernetes Job nested inside the ImageProcessingJob and Pods inside the Kubernetes Job
        ipj_details = {
            'image_processing_job': ipj,
            'k8s_job': {
                'details': k8s_job,
                'pods': pods
            }
        }

        return ipj_details
    
    except client.rest.ApiException as e:
        return {'error': f'Failed to retrieve details: {str(e)}'}