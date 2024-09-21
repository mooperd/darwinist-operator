from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kubernetes import client, config
import uuid

# Load Kubernetes configuration
config.load_incluster_config()  # Use this if running inside a cluster
# config.load_kube_config()     # Use this if running locally for testing

app = FastAPI()

# Define the request model
class ImageProcessingRequest(BaseModel):
    s3_input_location: str
    model_name: str
    s3_output_location: str

@app.post("/process-image/")
def process_image(request: ImageProcessingRequest):
    api_instance = client.CustomObjectsApi()
    group = 'example.com'
    version = 'v1'
    namespace = 'default'  # Change if needed
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
            's3_input_location': request.s3_input_location,
            'model_name': request.model_name,
            's3_output_location': request.s3_output_location,
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
        return {"message": "Image processing job created.", "job_name": resource_name}
    except client.rest.ApiException as e:
        raise HTTPException(status_code=500, detail=str(e))