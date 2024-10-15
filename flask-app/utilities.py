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