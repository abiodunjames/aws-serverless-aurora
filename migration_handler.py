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
    create_version_table()  # Create a table to store the migration versions

    SQL_PATH = "/opt"  # Layers are extracted to the /opt directory in the function execution environment.

    # This needs to change if there are to be multiple resources
    # in the same stack
    physical_id = "SchemaMigrationResource"

    try:
        log.info("Input event: %s", event)

        sqlfiles = glob.glob(os.path.join(SQL_PATH, "*.sql"))

        log.info(sqlfiles)
        for file_path in sqlfiles:
            version = Path(file_path).stem
            log.info(file_path)
            row = execute_statement(
                sql=f"select * from alembic_version where version_num=:version_num;",
                sql_parameters=[
                    {"name": "version_num", "value": {"stringValue": version}}
                ],
            )
            log.info(row)
            if len(row["records"]) == 0:
                execute_sql_file(file_path)

        log.info("Ran migration successfully")

        # Do the thing
        attributes = {"Response": f"Ran migration successfully:{sqlfiles}"}

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


def create_version_table():
    sql = f"CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));"
    execute_statement(sql)