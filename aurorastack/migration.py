from aws_cdk import (
    core,
    custom_resources as cr,
    aws_lambda as _lambda,
    aws_cloudformation as cfn,
    aws_iam as _iam,
)
from aws_cdk.aws_lambda import Runtime

SQL_SCRIPTS_PATH = "scripts/schema"


class SchemaMigrationResource(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        secret_arn: str,
        db_name: str,
        db_ref: str,
        **kwargs,
    ):
        super().__init__(
            scope,
            id,
            **kwargs,
        )

        with open("migration_handler.py", encoding="utf-8") as fp:
            code_body = fp.read()

            lambda_function = _lambda.SingletonFunction(
                self,
                "Singleton",
                uuid="f7d4f730-4ee1-11e8-9c2d-fa7ae01bbebc",
                code=_lambda.InlineCode(code_body),
                handler="index.main",
                timeout=core.Duration.seconds(300),
                runtime=_lambda.Runtime.PYTHON_3_7,
                layers=[
                    _lambda.LayerVersion(
                        scope,
                        id="migrationscripts",
                        code=_lambda.Code.from_asset(SQL_SCRIPTS_PATH),
                        description="Database migration scripts",
                    )
                ],
                environment={
                    "DB_NAME": db_name,
                    "DB_SECRET_ARN": secret_arn,
                    "DB_CLUSTER_ARN": db_ref,
                },
            )

        # Allow lambda to read database secret
        lambda_function.add_to_role_policy(
            _iam.PolicyStatement(
                resources=[secret_arn],
                actions=["secretsmanager:GetSecretValue"],
            )
        )
        # allow lambda to execute query on the database
        lambda_function.add_to_role_policy(
            _iam.PolicyStatement(
                resources=[db_ref],
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                ],
            )
        )
        # assign policies to the Lambda function so it can output to CloudWatch Logs.
        lambda_function.add_to_role_policy(
            _iam.PolicyStatement(
                resources=["*"],
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
            )
        )

        resource = cfn.CustomResource(
            self,
            "Resource",
            provider=cfn.CustomResourceProvider.lambda_(lambda_function),
            properties=kwargs,
        )

        self.response = resource.get_att("Response").to_string()
