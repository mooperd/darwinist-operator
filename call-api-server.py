import requests

def call_process_image(s3_input_location, model_name, s3_output_location, host='http://localhost:8000'):
    """
    Calls the /process-image/ endpoint to create an image processing job.

    Args:
        s3_input_location (str): The S3 input location.
        model_name (str): The name of the model to use.
        s3_output_location (str): The S3 output location.
        host (str): The base URL of the API (default is 'http://localhost:8000').

    Returns:
        dict: The JSON response from the API.

    Raises:
        Exception: If the API request fails.
    """
    # url = f"http://darwinist-api-server.apps.goose.hpc-l.com/process-image/"
    url = f"http://0.0.0.0:8080/process-image/"
    payload = {
        's3_input_location': s3_input_location,
        'model_name': model_name,
        's3_output_location': s3_output_location,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")
    
def main():
    call_process_image(
        "test 1",
        "test 2",
        "test 3"
    )

if __name__ == "__main__":
    main()