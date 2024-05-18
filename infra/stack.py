import os

import aws_cdk as cdk
from aws_cdk import (
    aws_s3,
    aws_events,
    aws_sns_subscriptions,
    aws_sns,
    aws_apigateway,
)
from constructs import Construct

from infra.components import Func, Table


class API(cdk.NestedStack):
    def __init__(self, scope, cid):
        super().__init__(scope, cid)
        self._make_api()

    def _make_api(self):
        self._make_api_lambdas()
        self._make_api_gateway()

    def _make_api_lambdas(self):
        self.proxy_lambda = Func(
            scope=self,
            cid="proxy",
            tag=os.environ["OCR_LAMBDA_TAG"],
            path="api/handler.lambda_handler",
            memory="1024",
            duration=cdk.Duration.seconds(30),
        )
        self.auth_lambda = Func(
            scope=self,
            cid="auth",
            tag=os.envirosn["OCR_LAMBDA_TAG"],
            path="auth/handler.lambda_handler",
            memory="1024",
            duration=cdk.Duration.seconds(30),
        )

    def _make_api_gateway(self):
        authorizer = aws_apigateway.RequestAuthorizer(
            scope=self, id="Authorizer", handler=self.auth_lambda.function
        )

        self.api = aws_apigateway.RestApi(
            scope=self,
            id="gateway",
            deploy=True,
            endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
            deploy_options=aws_apigateway.StageOptions(
                stage_name=os.environ["ENVIRONMENT"]
            ),
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=["*"]
            ),
        )

        # add auth proxy resource
        self.api.root.add_resource(
            "auth",
            default_integration=aws_apigateway.LambdaIntegration(
                handler=self.auth_lambda.function, proxy=True
            ),
            default_method_options=aws_apigateway.MethodOptions(
                authorizer=None,
                authorization_type=aws_apigateway.AuthorizationType.NONE,
            ),
        )

        # add swagger resource
        self.swagger_resource = self.api.root.add_resource(
            "swagger",
            default_method_options=aws_apigateway.MethodOptions(
                authorizer=None,
                authorization_type=aws_apigateway.AuthorizationType.NONE,
            ),
        )
        self.swagger_resource.add_method(
            http_method="GET",
            integration=aws_apigateway.LambdaIntegration(
                handler=self.proxy_lambda.function, proxy=True
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                )
            ],
        )

        # add proxy resource
        self.api.root.add_resource(
            "/{proxy+}",
            default_integration=aws_apigateway.LambdaIntegration(
                handler=self.proxy_lambda.function, proxy=True
            ),
            any_method=True,
            default_method_options=aws_apigateway.MethodOptions(
                authorizer=authorizer,
            ),
        )


class OCR(cdk.NestedStack):
    def __init__(self, scope, cid):
        super().__init__(scope, cid)
        self._make_ocr()

    def _make_ocr(self):
        self._make_ocr_lambdas()
        self._make_ocr_notifications()

    def _make_ocr_lambdas(self):
        self.preprocess_lambda = Func(
            scope=self,
            cid="preprocess",
            tag=os.environ["OCR_LAMBDA_TAG"],
            path="preprocess/handler.lambda_handler",
            memory="1024",
            duration=cdk.Duration.seconds(30),
        )
        self.postprocess_lambda = Func(
            scope=self,
            cid="postprocess",
            tag=os.environ["OCR_LAMBDA_TAG"],
            path="postprocess/handler.lambda_handler",
            memory="1024",
            duration=cdk.Duration.seconds(30),
        )

    def _make_ocr_notifications(self):
        self.sns_topic = aws_sns.Topic(
            scope=self,
            id="Topic",
            display_name="OCR-Topic",
            topic_name="ocr-topic",
        )
        self.event_bridge = aws_events.EventBus(scope=self, id="Bus")

        # make postprocess rule for lambda
        self.ocr_rule = aws_events.Rule(
            scope=self,
            id="Rule",
            event_bus=self.event_bridge,
            event_pattern=aws_events.EventPattern(
                source=["aws.sns"], resources=[self.sns_topic.topic_arn]
            ),
        )
        self.ocr_rule.add_target(self.postprocess_lambda.function)


class Main(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.table = Table(self, "Table")
        self.bucket = aws_s3.Bucket(
            self,
            "Bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        self.bridge = aws_events.EventBus(scope=self, id="Bus")
        self.sns = aws_sns.Topic(scope=self, id="Topic")

    def buid(self):
        self.api_stack = API(scope=self, cid="API")
        self.ocr_stack = OCR(scope=self, cid="OCR")
        self._update_lambdas()

    def _update_lambdas(self):

        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Func):
                self._grant_access(attr)
                self._add_environment_vars(attr)

    def _add_environment_vars(self, item: Func):

        vars = {
            "SNS_TOPIC_ARN": self.ocr_stack.sns_topic.topic_arn,
            "TABLE_NAME": self.table.table_name,
            "BUCKET_NAME": self.bucket.bucket_name,
            "BUS_NAME": self.bridge.event_bus_name,
        }
        for key, value in vars.items():
            item.function.add_environment(key, value)

    def _grant_access(self, item: Func):

        self.table.grant_read_write_data(item)
        self.bucket.grant_read_write(item)
        self.bridge.grant_put_events(item)
        self.sns.grant_publish(item)
