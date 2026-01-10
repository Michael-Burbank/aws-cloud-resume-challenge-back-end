import json
import boto3
import os

def _response(status_code: int, body: dict):
    return{
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }, 
        "body": json.dumps(body),
    }



def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello mike",
            # "location": ip.text.replace("\n", "")
        }),
    }
