import json
import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_authorizers as apigwv2_auth,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_rds as rds,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    triggers,
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
            "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-5-5",
            "TRANSFER_ACK_TIMEOUT_SECONDS": "60",
            "TRANSFER_UPLOAD_TIMEOUT_SECONDS": "600",
            "SWEEPER_MAX_AGE_MINUTES": "15",
            "UPLOAD_URL_EXPIRY_SECONDS": "600",
            "DOWNLOAD_URL_EXPIRY_SECONDS": "300",
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
            serverless_v2_max_capacity=2,  # headroom for the pgvector HNSW index (E6-S2)
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

        # ── Secrets Manager VPC endpoint (E1-S4) ─────────────────────────────
        # Lambdas are in isolated subnets with no NAT, so they can only reach
        # Secrets Manager (DB credentials) through an interface endpoint.
        endpoint_sg = ec2.SecurityGroup(self, "EndpointSg", vpc=vpc,
                                        description="VPC interface endpoints")
        endpoint_sg.add_ingress_rule(lambda_sg, ec2.Port.tcp(443), "Lambda to endpoints")
        vpc.add_interface_endpoint("SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[endpoint_sg],
        )

        # ── Shared Lambda settings ───────────────────────────────────────────
        lambdas_dir = os.path.join(os.path.dirname(__file__), "..", "central", "lambdas")
        lambda_env = {
            "DB_SECRET_ARN": db_secret.secret_arn,
            "DB_HOST": db.cluster_endpoint.hostname,
            "DB_PORT": "5432",
            "DB_NAME": "hivemind",
            "TRANSIT_BUCKET": transit_bucket.bucket_name,
            **{k: v for k, v in config.items()},
        }

        # psycopg2 built for Linux by infra/build_layer.py (no Docker needed).
        psycopg2_layer = lambda_.LayerVersion(self, "Psycopg2Layer",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "layer")),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="psycopg2-binary for Lambda (manylinux)",
        )

        def vpc_function(construct_id, handler, timeout=30):
            return lambda_.Function(self, construct_id,
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler=handler,
                code=lambda_.Code.from_asset(lambdas_dir),
                role=lambda_role,
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
                security_groups=[lambda_sg],
                environment=lambda_env,
                layers=[psycopg2_layer],
                timeout=Duration.seconds(timeout),
            )

        # ── Hello Lambda ─────────────────────────────────────────────────────
        hello_fn = vpc_function("HelloFn", "hello.handler")

        # ── Teams API (E1-S4) and DB migrations ──────────────────────────────
        teams_fn = vpc_function("TeamsFn", "teams.handler")
        files_fn = vpc_function("FilesFn", "files.handler")
        search_fn = vpc_function("SearchFn", "search.handler")
        migrate_fn = vpc_function("MigrateFn", "migrate.handler", timeout=120)

        # ── LLM proxy (E3-S3) ────────────────────────────────────────────────
        # Outside the VPC on purpose: the VPC subnets have no NAT so they cannot reach
        # Bedrock, and this function needs no database. Its own role, so it gets no DB/S3.
        llm_role = iam.Role(self, "LlmRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        # Converse needs bedrock:InvokeModel. The inference-profile ARN keeps this working if
        # BEDROCK_MODEL_ID has to become a cross-region inference profile.
        llm_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                "arn:aws:bedrock:*::foundation-model/anthropic.*",
                f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/*",
            ],
        ))
        llm_fn = lambda_.Function(self, "LlmFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="llm.handler",
            code=lambda_.Code.from_asset(lambdas_dir),
            role=llm_role,
            environment={k: config[k] for k in ("BEDROCK_MODEL_ID", "EXCERPT_MAX_CHARS")},
            timeout=Duration.seconds(25),
        )
        # ── Relay WebSocket (E4-S1) ──────────────────────────────────────────
        # The authorizer is outside the VPC for the same reason as llm_fn: it must fetch
        # Cognito's JWKS over the internet. It needs no DB, so it gets a basic role only.
        auth_layer = lambda_.LayerVersion(self, "AuthLayer",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "auth_layer")),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="PyJWT + cryptography for the WebSocket authorizer (manylinux)",
        )
        ws_authorizer_role = iam.Role(self, "WsAuthorizerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        ws_authorizer_fn = lambda_.Function(self, "WsAuthorizerFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="ws_authorizer.handler",
            code=lambda_.Code.from_asset(lambdas_dir),
            role=ws_authorizer_role,
            layers=[auth_layer],
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
            },
            timeout=Duration.seconds(10),
        )
        relay_fn = vpc_function("RelayFn", "relay.handler", timeout=10)

        ws_api = apigwv2.WebSocketApi(self, "RelayWsApi",
            route_selection_expression="$request.body.action",
        )
        ws_api.add_route("$connect",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("WsConnectIntegration", relay_fn),
            # Agents are not browsers, so the token travels in the Authorization header
            # rather than a query string that would end up in URLs and logs.
            authorizer=apigwv2_auth.WebSocketLambdaAuthorizer(
                "WsJwtAuthorizer", ws_authorizer_fn,
                identity_source=["route.request.header.Authorization"],
            ),
        )
        ws_api.add_route("$disconnect",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("WsDisconnectIntegration", relay_fn),
        )
        ws_api.add_route("ping",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("WsPingIntegration", relay_fn),
            return_response=True,  # the handler's body is sent back to the client as the pong
        )
        ws_stage = apigwv2.WebSocketStage(self, "RelayWsStage",
            web_socket_api=ws_api, stage_name="dev", auto_deploy=True,
        )

        # ── Transfer API (E4-S2) ─────────────────────────────────────────────
        # Notifying the owner means calling the WebSocket management API. From inside the VPC that
        # call was refused (ForbiddenException) when routed through an execute-api interface
        # endpoint, though IAM allowed it and the same call works outside the VPC. So the send is
        # done by a small non-VPC Lambda (no DB access), which the VPC-bound transfers Lambda
        # invokes through a Lambda interface endpoint.
        notify_role = iam.Role(self, "NotifyRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        notify_role.add_to_policy(iam.PolicyStatement(
            actions=["execute-api:ManageConnections"],
            resources=[f"arn:{self.partition}:execute-api:{self.region}:{self.account}:"
                       f"{ws_api.api_id}/{ws_stage.stage_name}/POST/@connections/*"],
        ))
        notify_fn = lambda_.Function(self, "NotifyFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="notify.handler",
            code=lambda_.Code.from_asset(lambdas_dir),
            role=notify_role,
            environment={"WS_MANAGEMENT_URL": ws_stage.callback_url},
            timeout=Duration.seconds(15),
        )
        vpc.add_interface_endpoint("LambdaEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.LAMBDA_,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[endpoint_sg],
        )
        notify_fn.grant_invoke(lambda_role)
        transfers_fn = vpc_function("TransfersFn", "transfers.handler")
        transfers_fn.add_environment("NOTIFY_FUNCTION_NAME", notify_fn.function_name)

        # ── Transfer sweeper (E4-S5) ─────────────────────────────────────────
        # Needs the DB, so it lives in the VPC, and the VPC has no NAT: a free S3 gateway
        # endpoint lets it delete transit objects. lambda_role already has bucket read/write.
        vpc.add_gateway_endpoint("S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)],
        )
        sweeper_fn = vpc_function("SweeperFn", "sweeper.handler", timeout=60)
        events.Rule(self, "SweeperSchedule",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            targets=[targets.LambdaFunction(sweeper_fn)],
        )
        cdk.CfnOutput(self, "SweeperFunctionName", value=sweeper_fn.function_name,
                       description="Transfer sweeper Lambda (integration tests invoke it directly)")

        # Runs migrate_fn on every deploy where its code changed. Idempotent
        # (applies each migrations/*.sql once); a failure fails the deploy.
        triggers.Trigger(self, "RunMigrations",
            handler=migrate_fn,
            execute_after=[db],
            execute_on_handler_change=True,
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

        def add_authed_route(path, methods, fn, integration_id):
            """Every Interface B route goes through here so the JWT authorizer
            is the default. Only /health is registered without it (below)."""
            http_api.add_routes(
                path=path,
                methods=methods,
                integration=apigwv2_integrations.HttpLambdaIntegration(integration_id, fn),
                authorizer=jwt_authorizer,
            )

        add_authed_route("/hello", [apigwv2.HttpMethod.GET], hello_fn, "HelloIntegration")

        for path, methods, integration_id in [
            ("/teams", [apigwv2.HttpMethod.POST], "TeamsCreateIntegration"),
            ("/teams/me", [apigwv2.HttpMethod.GET], "TeamsMeIntegration"),
            ("/teams/me/email", [apigwv2.HttpMethod.PUT], "TeamsEmailIntegration"),
            ("/teams/me/invites", [apigwv2.HttpMethod.POST], "TeamsInvitesIntegration"),
            ("/teams/join", [apigwv2.HttpMethod.POST], "TeamsJoinIntegration"),
            ("/teams/me/leave", [apigwv2.HttpMethod.POST], "TeamsLeaveIntegration"),
        ]:
            add_authed_route(path, methods, teams_fn, integration_id)

        # Metadata API (E3-S2)
        for path, methods, integration_id in [
            ("/files/{file_id}", [apigwv2.HttpMethod.PUT, apigwv2.HttpMethod.DELETE], "FilesItemIntegration"),
            ("/files/{file_id}/confirm", [apigwv2.HttpMethod.POST], "FilesConfirmIntegration"),
            ("/files/mine", [apigwv2.HttpMethod.GET], "FilesMineIntegration"),
        ]:
            add_authed_route(path, methods, files_fn, integration_id)

        # Transfer API (E4-S2)
        for path, methods, integration_id in [
            ("/transfers", [apigwv2.HttpMethod.POST], "TransfersCreateIntegration"),
            ("/transfers/{transfer_id}", [apigwv2.HttpMethod.GET], "TransfersGetIntegration"),
            ("/transfers/{transfer_id}/ack", [apigwv2.HttpMethod.POST], "TransfersAckIntegration"),
            ("/transfers/{transfer_id}/complete", [apigwv2.HttpMethod.POST], "TransfersCompleteIntegration"),
            ("/transfers/{transfer_id}/fail", [apigwv2.HttpMethod.POST], "TransfersFailIntegration"),
        ]:
            add_authed_route(path, methods, transfers_fn, integration_id)

        # Central search (E3-S7)
        add_authed_route("/search", [apigwv2.HttpMethod.POST], search_fn, "SearchIntegration")

        # LLM proxy (E3-S3)
        add_authed_route("/llm/tags", [apigwv2.HttpMethod.POST], llm_fn, "LlmTagsIntegration")

        # Unauthenticated health check: the one deliberate exception
        health_fn = lambda_.Function(self, "HealthFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="health.handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "central", "lambdas")
            ),
            timeout=Duration.seconds(10),
        )
        http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integrations.HttpLambdaIntegration("HealthIntegration", health_fn),
        )

        # ── Outputs ──────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "HttpApiUrl", value=http_api.api_endpoint,
                       description="Central HTTP API base URL — put in agent config")
        cdk.CfnOutput(self, "WebSocketUrl", value=ws_stage.url,
                       description="Relay WebSocket URL (wss) — put in agent config")
        cdk.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id,
                       description="Cognito User Pool ID — put in agent config")
        cdk.CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id,
                       description="Cognito App Client ID — put in agent config")
        cdk.CfnOutput(self, "TransitBucketName", value=transit_bucket.bucket_name,
                       description="S3 transit bucket name")
        cdk.CfnOutput(self, "DbSecretArn", value=db_secret.secret_arn,
                       description="Secrets Manager ARN for DB credentials")
