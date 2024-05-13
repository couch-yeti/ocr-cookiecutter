import os

import aws_cdk as cdk
from aws_cdk import (
    aws_s3,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_sns,
    aws_apigateway,
)

from components import Func, Table


class API(cdk.NestedStack):
    def __init__(self, scope, cid):
        super().__init__(scope, cid)

    def _make_api_lambdas(self):
        self.proxy_lambda = Func(
            scope=self,
            cid="proxy",
            tag=os.environ["PROXY_LAMBDA_TAG"],
            path="api/handler.lambda_handler",
            memory="1024",
            duration=cdk.Duration.seconds(30),
        )
        self.auth_lambda = Func(
            scope=self,
            cid="auth",
            tag=os.envirosn["AUTH_LAMBDA_TAG"],
            path="auth/handler.lambda_handler",
            memory="1024",
            duration=cdk.Duration.seconds(30),
        )

    def _make_api_gateway(self):
        authorizer = aws_apigateway.RequestAuthorizer(
            scope=self, id="Authorizer", handler=self.auth_lambda.function
        )


class Main(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.table = Table(self, "Table")
        self.bucket = aws_s3.Bucket(
            self,
            "Bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        self.bridge = aws_events.EventBus(scope=self, id="Bus")
        self.sns = aws_sns.Topic(scope=self, id="Topic")
