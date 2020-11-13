#!/usr/bin/env python3

from aws_cdk import core
import os
from aurorastack.api import Api
from aurorastack.rds import RDSStack
from aurorastack.migration import SchemaMigrationResource

# https://docs.aws.amazon.com/cdk/latest/guide/environments.html
env_EU = core.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]),
)

app = core.App()
db = RDSStack(scope=app, id="aurora", env=env_EU)
ap_stack = Api(scope=app, id="api", env=env_EU, db=db)

app.synth()
