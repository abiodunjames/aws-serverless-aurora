from aurorastack.rds import RDSStack
from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_apigateway as _apigw,
    aws_iam as _iam,
)
from aurorastack.utils import add_cors_options
from aurorastack.config import routes

class Api(core.Stack):
    def __init__(self, scope: core.Construct, id: str, db: RDSStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.api = _apigw.RestApi(
            self, "ApiGatewayWithCors", rest_api_name="ApiGatewayWithCors"
        )
        self.db = db
        for resource in routes.keys():
            route_details = routes[resource]
            api_resource = self.create_resource(resource)
            for route in route_details:
                lambda_function = self.create_lambda_function(route["function"])
                self.add_policy(lambda_function)
                integrated_resource = self.integrate_resource(lambda_function)
                self.create_method(api_resource, integrated_resource, route["method"])
            self.add_cors(api_resource)

    def create_lambda_function(self, lambda_function: str) -> _lambda.Function:
        """Create a lnabda function object with environment variables.
        Args:
            lambda_function: the name of the lambda function.

        Returns:
            This returns a lambda function object.

        """
        return _lambda.Function(
            self,
            lambda_function,
            handler=f"{lambda_function}.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset("functions"),
            environment={
                "DB_NAME": self.db.db.database_name,
                "DB_SECRET_ARN": self.db.secret.secret_arn,
                "DB_CLUSTER_ARN": f"arn:aws:rds:{self.region}:{self.account}:cluster:{self.db.db.ref}",
            },
        )

    def create_resource(self, resource: str) -> _apigw.IResource:
        """Create an API Gateway resource.
        Args:
            resource: The resource name

        Returns:
            This returns a resource object.

        """
        return self.api.root.add_resource(resource)

    def integrate_resource(self, lambda_function) -> _apigw.LambdaIntegration:
        """Create a lambda integration.
        Args:
            resource: The resource name

        Returns:
            This returns a resource object.

        """

        return _apigw.LambdaIntegration(
            lambda_function,
            proxy=False,
            integration_responses=[
                {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                    },
                }
            ],
        )

    def create_method(
        self, resource: _apigw.IResource, integrated_resource, method: str
    ) -> None:

        """Create a lambda integration.
        Args:
            resource: The resource object
            integrated_resource: Integrated resource
            method: The http method

        Returns:
            None.

        """

        resource.add_method(
            method,
            integrated_resource,
            method_responses=[
                {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                }
            ],
        )

    def add_cors(self, resource):
        """Enable course on the endpoint
        Args:
            resource: The resource object

        Returns:
            None.

        """
        add_cors_options(resource)

    def add_policy(self, lambda_function: _lambda.Function) -> None:
        """Add necessary permissions to the lambda function. If you need your functions to have
            more permissions, you can add them below.
        Args:
            lambda_function: The lambda function

        Returns:
            None.

        """
        smt1 = _iam.PolicyStatement(
            resources=[self.db.secret.secret_arn],
            actions=["secretsmanager:GetSecretValue"],
        )
        lambda_function.add_to_role_policy(smt1)
        smt2 = _iam.PolicyStatement(
            resources=[
                f"arn:aws:rds:{self.region}:{self.account}:cluster:{self.db.db.ref}"
            ],
            actions=[
                "rds-data:ExecuteStatement",
                "rds-data:BatchExecuteStatement",
                "rds-data:BeginTransaction",
                "rds-data:CommitTransaction",
                "rds-data:ExecuteSql",
                "rds-data:RollbackTransaction",
                "rds:DescribeDBClusters",
            ],
        )
        lambda_function.add_to_role_policy(smt2)
