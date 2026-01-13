import json
import os
import boto3


# Helper func to format HTTP responses using an API Gateway proxy integration / response. 
def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _method(event: dict) -> str:
    # HTTP v1 - This version is checked first. 
    if "httpMethod" in event:
        return event["httpMethod"].upper()

    # HTTP v2 - This version is checked second && is a fallback.
    return (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "GET")
        .upper()
    )


def _ddb_resource():
    # USE ONLY FOR DynamoDB LOCAL testing (sam local).
    endpoint_url = os.getenv("DDB_ENDPOINT_URL")
    if endpoint_url:
        return boto3.resource("dynamodb", endpoint_url=endpoint_url)
    return boto3.resource("dynamodb")


def lambda_handler(event, context):
    # DynamoDB table name.
    table_name = os.getenv("TABLE_NAME", "Visitor_Count")  
    table = _ddb_resource().Table(table_name)

    key = {"id": "visitor_count"}
    method = _method(event)

    # Handle GET request.
    # Retrieves current visitor count from DynamoDB.
    if method == "GET":
        resp = table.get_item(Key=key)
        count = int(resp.get("Item", {}).get("count", 0))
        return _response(200, {"count": count})

    # Handle POST or PUT request.
    # Increments visitor count in DynamoDB.
    if method in ("POST", "PUT"):
        resp = table.update_item(
            Key=key,
            UpdateExpression="SET #c = if_not_exists(#c, :zero) + :inc",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":inc": 1, ":zero": 0},
            ReturnValues="UPDATED_NEW",
        )
        count = int(resp["Attributes"]["count"])
        return _response(200, {"count": count})

    return _response(405, {"error": f"Method not allowed: {method}"})