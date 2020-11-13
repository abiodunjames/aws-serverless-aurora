from aws_cdk import aws_apigateway as _apigw


def add_cors_options(apigw_resource: _apigw.Resource) -> None:
    """Enbale cors on API Gateway resource
    Args:
        apigw_resource: Api gateway resource
    """
    apigw_resource.add_method(
        "OPTIONS",
        _apigw.MockIntegration(
            integration_responses=[
                {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
                    },
                }
            ],
            passthrough_behavior=_apigw.PassthroughBehavior.WHEN_NO_MATCH,
            request_templates={"application/json": '{"statusCode":200}'},
        ),
        method_responses=[
            {
                "statusCode": "200",
                "responseParameters": {
                    "method.response.header.Access-Control-Allow-Headers": True,
                    "method.response.header.Access-Control-Allow-Methods": True,
                    "method.response.header.Access-Control-Allow-Origin": True,
                },
            }
        ],
    )