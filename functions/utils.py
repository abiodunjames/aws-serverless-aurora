import logging
import boto3
import os

log = logging.getLogger()
log.setLevel(logging.INFO)


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
        raise e
