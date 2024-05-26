import os

import aws_cdk as cdk
from aws_cdk import aws_lambda, aws_dynamodb, aws_ecr
from constructs import Construct


class Func(Construct):
    def __init__(
        self,
        scope: Construct,
        cid: str,
        tag: str,
        path: str,
        memory: str,
        duration: cdk.Duration,
    ):
        super().__init__(scope=scope, id=cid)
        self.function = aws_lambda.DockerImageFunction(
            scope=self,
            id=cid,
            code=aws_lambda.DockerImageCode.from_ecr(
                repository=self._get_repo(), tag_or_digest=tag, cmd=[path]
            ),
            memory_size=memory,
            timeout=duration,
        )

    def _get_repo(self):
        return aws_ecr.Repository.from_repository_name(
            scope=self,
            id="Repo",
            repository_name=os.environ["PROJECT_NAME"],
        )


class Table(Construct):
    def __init__(self, scope: Construct, cid: str):
        super().__init__(scope=scope, id=cid)
        self.table = aws_dynamodb.Table(
            scope=self,
            id=cid,
            partition_key=aws_dynamodb.Attribute(
                name="pk", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="sk", type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            time_to_live_attribute="expiration",
        )
