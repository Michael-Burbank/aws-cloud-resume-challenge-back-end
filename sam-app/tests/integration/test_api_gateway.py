# LOCAL TESTING SETUP:
import os
from urllib import response

import boto3
import pytest
import requests


# First checks if the .env file exists in the tests directory.
# If it does, it loads the environment variables from it.
@pytest.fixture(scope="session")
def check_secret_var():
    # Only load .env if not running in CI/CD
    if not os.environ.get("CI"):
        env_path = os.path.join("tests", ".env")
        if os.path.exists(env_path):
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_path)
        else:
            raise ValueError("Please create a .env file in the tests directory with the required environment variables.")

# Relies on the check_secret_var fixture to ensure .env file exists in tests directory prior to running this fixture.
@pytest.fixture
def api_gateway_url(check_secret_var):
    """Get the API Gateway URL from Cloudformation Stack outputs"""
    stack_name = os.environ.get("AWS_SAM_STACK_NAME")

    if stack_name is None:
        raise ValueError(
            "Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack"
        )

    client = boto3.client("cloudformation")

    try:
        response = client.describe_stacks(StackName=stack_name)
    except Exception as e:
        raise Exception(
            f"Cannot find stack {stack_name} \n"
            f'Please make sure a stack with the name "{stack_name}" exists'
        ) from e

    stacks = response["Stacks"]
    stack_outputs = stacks[0].get("Outputs")
    if not stack_outputs:
        raise KeyError(f"No outputs found for stack {stack_name}")

    api_outputs = [
        output
        for output in stack_outputs
        if output.get("OutputKey") == "VisitorCountApi"
    ]

    if not api_outputs:
        raise KeyError(f"VisitorCountApi not found in stack {stack_name}")

    if not api_outputs[0].get("OutputValue"):
        raise ValueError(
            "VisitorCountApi output value is empty. Please check your stack outputs."
        )  # Extract url from stack outputs.
    else:
        return api_outputs[0].get("OutputValue")


def test_api_gateway(api_gateway_url):
    """Call the API Gateway endpoint and check the response"""
    response = requests.get(api_gateway_url)

    # Matches the expected structure of the response from the lambda_handler function in app.py.
    assert response.status_code == 200
    assert "count" in response.json()
    assert isinstance(response.json()["count"], int)
