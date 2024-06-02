import os

import aws_cdk as cdk
from aws_cdk import (
    aws_s3,
    aws_s3_notifications,
    aws_events,
    aws_events_targets,
    aws_sns,
    aws_apigateway,
    aws_iam,
    aws_sqs,
    aws_sns_subscriptions as sns_subs,
    aws_lambda_event_sources as lambda_sources,
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
            path="api.handler.lambda_handler",
            memory=1024,
            duration=cdk.Duration.seconds(30),
        )
        self.auth_lambda = Func(
            scope=self,
            cid="auth",
            tag=os.environ["OCR_LAMBDA_TAG"],
            path="auth.handler.lambda_handler",
            memory=1024,
            duration=cdk.Duration.seconds(30),
        )

    def _make_api_gateway(self):
        authorizer = aws_apigateway.RequestAuthorizer(
            scope=self,
            id="Authorizer",
            handler=self.auth_lambda.function,
            identity_sources=[
                aws_apigateway.IdentitySource.header("authorizationToken")
            ],
        )

        self.api = aws_apigateway.RestApi(
            scope=self,
            id=f"{os.environ['PROJECT_NAME']}-api",
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
        self.api.root.add_proxy(
            default_integration=aws_apigateway.LambdaIntegration(
                handler=self.proxy_lambda.function
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
        self._grant_textract_access()

    def _make_ocr_lambdas(self):
        self.preprocess_lambda = Func(
            scope=self,
            cid="preprocess",
            tag=os.environ["OCR_LAMBDA_TAG"],
            path="preprocess.handler.lambda_handler",
            memory=1024,
            duration=cdk.Duration.seconds(30),
        )
        self.postprocess_lambda = Func(
            scope=self,
            cid="postprocess",
            tag=os.environ["OCR_LAMBDA_TAG"],
            path="postprocess.handler.lambda_handler",
            memory=1024,
            duration=cdk.Duration.seconds(30),
        )

    def _grant_textract_access(self):
        actions = [
            "textract:StartDocumentTextDetection",
            "textract:StartDocumentAnalysis",
            "textract:GetDocumentTextDetection",
            "textract:GetDocumentAnalysis",
        ]
        policy = aws_iam.PolicyStatement(actions=actions, resources=["*"])
        self.preprocess_lambda.function.add_to_role_policy(statement=policy)
        self.postprocess_lambda.function.add_to_role_policy(statement=policy)

    def _make_ocr_notifications(self):

        self.textract_role = aws_iam.Role(
            self,
            "TextractRole",
            assumed_by=aws_iam.ServicePrincipal("textract.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonTextractServiceRole"
                )
            ],
        )
        self.sns_topic = aws_sns.Topic(
            scope=self,
            id="Topic",
            display_name="OCR-Topic",
            topic_name="ocr-topic",
        )

        self.dlq = aws_sqs.Queue(self, "DLQ", queue_name="ocr-dlq")
        self.sqs_queue = aws_sqs.Queue(
            self,
            "Queue",
            queue_name="ocr-queue",
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=5, queue=self.dlq
            ),
            visibility_timeout=cdk.Duration.seconds(30),
        )

        self.sns_topic.grant_publish(self.textract_role)
        self.sns_topic.add_subscription(
            sns_subs.SqsSubscription(self.sqs_queue)
        )
        self.postprocess_lambda.function.add_event_source(
            lambda_sources.SqsEventSource(self.sqs_queue)
        )


class Main(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.table = Table(self, "Table").table
        self.bucket = aws_s3.Bucket(
            self,
            "Bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        self.bridge = aws_events.EventBus(scope=self, id="Bus")
        self.sns = aws_sns.Topic(scope=self, id="Topic")
        self.build()

    def build(self):
        self.api_stack = API(scope=self, cid="API")
        self.ocr_stack = OCR(scope=self, cid="OCR")
        self.bucket.add_event_notification(
            aws_s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.LambdaDestination(
                self.ocr_stack.preprocess_lambda.function
            ),
            aws_s3.NotificationKeyFilter(prefix="input/"),
        )
        self._update_lambdas(self.api_stack)
        self._update_lambdas(self.ocr_stack)

    def _update_lambdas(self, stack):

        for attr_name in dir(stack):
            attr = getattr(stack, attr_name)
            if isinstance(attr, Func):
                self._grant_access(attr)
                self._add_environment_vars(attr)

    def _add_environment_vars(self, item: Func):

        vars = {
            "TEXTRACT_ROLE_ARN": self.ocr_stack.textract_role.role_arn,
            "SNS_TOPIC_ARN": self.ocr_stack.sns_topic.topic_arn,
            "TABLE_NAME": self.table.table_name,
            "BUCKET_NAME": self.bucket.bucket_name,
            "BUS_NAME": self.bridge.event_bus_name,
            "LOG_LEVEL": "INFO",
            "PROJECT_NAME": os.environ["PROJECT_NAME"],
        }
        for key, value in vars.items():
            item.function.add_environment(key, value)

    def _grant_access(self, item: Func):

        self.table.grant_read_write_data(item.function)
        self.bucket.grant_read_write(item.function)
        self.bridge.grant_put_events_to(item.function)
        self.sns.grant_publish(item.function)
