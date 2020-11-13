import boto3
import os
import logging as log

from botocore import exceptions
import cfnresponse
import glob
from pathlib import Path
import re

log.getLogger().setLevel(log.INFO)


def main(event, context):
    SQL_PATH = "/opt"  # Layers are extracted to the /opt directory in the function execution environment.

    # This needs to change if there are to be multiple resources
    # in the same stack
    physical_id = "SchemaMigrationResource"

    # If this is a Delete event, do nothing. The schema will be destroyed along with the cluster.
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Response": "Deleted successfully"}, physical_id)

    try:
        log.info("Input event: %s", event)

        sqlfiles = glob.glob(os.path.join(SQL_PATH, "*.sql"))

        log.info(sqlfiles)
        for file_path in sqlfiles:
            log.info(f"Found an SQL script in path:{file_path}")
            execute_sql_file(file_path)

        log.info("Ran migration successfully")

        # Do the thing
        attributes = {"Response": f"Ran migration successfully for these files:{sqlfiles}"}

        cfnresponse.send(event, context, cfnresponse.SUCCESS, attributes, physical_id)
    except Exception as e:
        log.exception(e)
        # cfnresponse's error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
        raise RuntimeError("Create failure requested")


def execute_statement(sql, sql_parameters=[], transaction_id=None):
    log.info(f"sql query:{sql}")
    client = boto3.client("rds-data")
    parameters = {
        "secretArn": os.getenv("DB_SECRET_ARN"),
        "database": os.getenv("DB_NAME"),
        "resourceArn": os.getenv("DB_CLUSTER_ARN"),
        "sql": sql,
        "parameters": sql_parameters,
    }
    if transaction_id is not None:
        parameters["transactionId"] = transaction_id
    try:
        response = client.execute_statement(**parameters)
        return response
    except client.exceptions.BadRequestException as e:
        log.exception(e)
        raise RuntimeError("Create failure requested")


def execute_sql_file(file_path: str):
    log.info(f"executing file in : {file_path}")
    with open(file_path, "r") as script:
        script_content = script.read()
        queries = script_content.split(";")
        for query in queries:
            sql = query.strip()
            if sql:
                execute_statement(query)
    log.info(f"executed the file : {file_path} successfully")
