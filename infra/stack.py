import json
import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_authorizers as apigwv2_auth,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_rds as rds,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
)
from constructs import Construct


class HiveMindStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Config values (E0-S2 acceptance criterion) ─────────────────────
        config = {
            "RETENTION_DAYS": "45",
            "EXPIRING_SOON_DAYS": "7",
            "INVITE_LIFETIME_DAYS": "7",
            "EXCERPT_MAX_CHARS": "3000",
            "SEARCH_RESULT_CAP": "20",
            "PUBLISH_CONCURRENCY": "5",
            "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-5-5",
            "TRANSFER_ACK_TIMEOUT_SECONDS": "60",
            "SWEEPER_MAX_AGE_MINUTES": "15",
        }
        for key, value in config.items():
            ssm.StringParameter(self, f"Param{key}",
                parameter_name=f"/hivemind/{key.lower()}",
                string_value=value,
            )

        # ── VPC ─────────────────────────────────────────────────────────────
        vpc = ec2.Vpc(self, "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )

        # ── Security groups ─────────────────────────────────────────────────
        lambda_sg = ec2.SecurityGroup(self, "LambdaSg", vpc=vpc, description="Lambda to RDS")
        rds_sg = ec2.SecurityGroup(self, "RdsSg", vpc=vpc, description="RDS")
        rds_sg.add_ingress_rule(lambda_sg, ec2.Port.tcp(5432), "Lambda access")

        # ── Aurora Serverless v2 (Postgres-compatible) ───────────────────────
        # Standard RDS CreateDBInstance is blocked by org policy; Aurora
        # Serverless v2 uses CreateDBCluster which is permitted.
        db_secret = rds.DatabaseSecret(self, "DbSecret",
            username="hivemind",
            secret_name="hivemind/db-credentials",
        )
        db = rds.DatabaseCluster(self, "Db",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.of("16.8", "16")
            ),
            credentials=rds.Credentials.from_secret(db_secret),
            default_database_name="hivemind",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[rds_sg],
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=1,
            writer=rds.ClusterInstance.serverless_v2("writer"),
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
        )

        # ── S3 transit bucket ────────────────────────────────────────────────
        transit_bucket = s3.Bucket(self, "TransitBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                # Day-level backstop in case the sweeper Lambda fails
                s3.LifecycleRule(expiration=Duration.days(1))
            ],
        )

        # ── Cognito User Pool (E0-S3) ────────────────────────────────────────
        pre_signup_fn = lambda_.Function(self, "PreSignupFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="pre_signup.handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "central", "lambdas")
            ),
            timeout=Duration.seconds(10),
        )

        user_pool = cognito.UserPool(self, "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=False),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
            ),
            lambda_triggers=cognito.UserPoolTriggers(
                pre_sign_up=pre_signup_fn,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # App client: password auth flow, no client secret (E0-S3)
        user_pool_client = user_pool.add_client("AgentClient",
            auth_flows=cognito.AuthFlow(user_password=True),
            generate_secret=False,
        )

        # ── Lambda execution role ────────────────────────────────────────────
        lambda_role = iam.Role(self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ],
        )
        db_secret.grant_read(lambda_role)
        transit_bucket.grant_read_write(lambda_role)

        # ── Hello Lambda ─────────────────────────────────────────────────────
        hello_fn = lambda_.Function(self, "HelloFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="hello.handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "central", "lambdas")
            ),
            role=lambda_role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[lambda_sg],
            environment={
                "DB_SECRET_ARN": db_secret.secret_arn,
                "DB_HOST": db.cluster_endpoint.hostname,
                "DB_PORT": "5432",
                "DB_NAME": "hivemind",
                "TRANSIT_BUCKET": transit_bucket.bucket_name,
                **{k: v for k, v in config.items()},
            },
            timeout=Duration.seconds(30),
        )

        # ── HTTP API Gateway (E0-S3 JWT authorizer) ──────────────────────────
        # Decision (E0-S3): use the ACCESS token (not ID token) — sub is stable
        # and access tokens are the standard for API authorization.
        http_api = apigwv2.HttpApi(self, "HttpApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_headers=["Authorization", "Content-Type"],
            ),
        )

        jwt_authorizer = apigwv2_auth.HttpJwtAuthorizer(
            "CognitoAuthorizer",
            jwt_issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool.user_pool_id}",
            jwt_audience=[user_pool_client.user_pool_client_id],
        )

        hello_integration = apigwv2_integrations.HttpLambdaIntegration(
            "HelloIntegration", hello_fn
        )
        http_api.add_routes(
            path="/hello",
            methods=[apigwv2.HttpMethod.GET],
            integration=hello_integration,
            authorizer=jwt_authorizer,
        )
        # Unauthenticated health check
        http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=hello_integration,
        )

        # ── Outputs ──────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "HttpApiUrl", value=http_api.api_endpoint,
                       description="Central HTTP API base URL — put in agent config")
        cdk.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id,
                       description="Cognito User Pool ID — put in agent config")
        cdk.CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id,
                       description="Cognito App Client ID — put in agent config")
        cdk.CfnOutput(self, "TransitBucketName", value=transit_bucket.bucket_name,
                       description="S3 transit bucket name")
        cdk.CfnOutput(self, "DbSecretArn", value=db_secret.secret_arn,
                       description="Secrets Manager ARN for DB credentials")
