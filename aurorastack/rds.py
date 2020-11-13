#!/usr/bin/env python3
import os
from aws_cdk import (
    aws_ec2 as ec2,  # pip install aws_cdk.aws_ec2
    aws_rds as rds,  # pip install aws_cdk.aws_rds
    core,
    aws_secretsmanager as sm,
)
from .migration import SchemaMigrationResource


class RDSStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, "VPC")
        db_master_user_name = os.getenv("DB_USERNAME", "admin_user")

        self.secret = rds.DatabaseSecret(
            self, id="MasterUserSecret", username=db_master_user_name
        )

        rds.CfnDBSubnetGroup(
            self,
            "rdsSubnetGroup",
            db_subnet_group_description="private subnets for rds",
            subnet_ids=vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE
            ).subnet_ids,
        )
        db_name = os.getenv("DB_NAME", "anonfed")
        self.db = rds.CfnDBCluster(
            self,
            "auroraCluster",
            engine="aurora-mysql",
            engine_version="5.7.mysql_aurora.2.08.1",
            db_cluster_parameter_group_name="default.aurora-mysql5.7",
            # snapshot_identifier="<snapshot_arn>",  # your snapshot
            engine_mode="serverless",
            scaling_configuration=rds.CfnDBCluster.ScalingConfigurationProperty(
                auto_pause=True,
                min_capacity=1,
                max_capacity=4,
                seconds_until_auto_pause=300,
            ),
            db_subnet_group_name=core.Fn.ref("rdsSubnetGroup"),
            database_name=db_name,
            master_username=self.secret.secret_value_from_json("username").to_string(),
            master_user_password=self.secret.secret_value_from_json(
                "password"
            ).to_string(),
            enable_http_endpoint=True,
        )

        secret_attached = sm.CfnSecretTargetAttachment(
            self,
            id="secret_attachment",
            secret_id=self.secret.secret_arn,
            target_id=self.db.ref,
            target_type="AWS::RDS::DBCluster",
        )
        secret_attached.node.add_dependency(self.db)
        db_ref = f"arn:aws:rds:{self.region}:{self.account}:cluster:{self.db.ref}"
        migration = SchemaMigrationResource(
            self, "schemamigration", self.secret.secret_arn, db_name, db_ref
        )

        # Publish the custom resource output
        core.CfnOutput(
            self,
            "ResponseMessage",
            description="Database Migration",
            value=migration.response,
        )

        core.CfnOutput(
            self,
            id="DatabaseName",
            value=self.db.database_name,
            description="Database Name",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:database-name",
        )

        core.CfnOutput(
            self,
            id="DatabaseClusterArn",
            value=db_ref,
            description="Database Cluster Arn",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:database-cluster-arn",
        )

        core.CfnOutput(
            self,
            id="DatabaseSecretArn",
            value=self.secret.secret_arn,
            description="Database Secret Arn",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:database-secret-arn",
        )

        core.CfnOutput(
            self,
            id="AuroraEndpointAddress",
            value=self.db.attr_endpoint_address,
            description="Aurora Endpoint Address",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:aurora-endpoint-address",
        )

        core.CfnOutput(
            self,
            id="DatabaseMasterUserName",
            value=db_master_user_name,
            description="Database Master User Name",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:database-master-username",
        )
