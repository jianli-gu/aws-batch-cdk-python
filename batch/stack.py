from aws_cdk import core
from aws_cdk import aws_batch as batch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_secretsmanager as secretsmanager


STACK_PREFIX = "solar"

# Network
VPC_ID = STACK_PREFIX + "-vpc-id"
SECURITY_GROUP_ID = STACK_PREFIX + "-sg-id"
SECURITY_GROUP_NAME = STACK_PREFIX + "-sg"

# Roles
BATCH_SERVICE_ROLE_ID = STACK_PREFIX + "-batch-service-role-id"
BATCH_SERVICE_ROLE_NAME = STACK_PREFIX + "-batch-service-role"

SPOT_FLEET_ROLE_ID = STACK_PREFIX + "-spot-fleet-role-id"
SPOT_FLEET_ROLE_NAME = STACK_PREFIX + "-spot-fleet-role"

BATCH_INSTANCE_ROLE_ID = STACK_PREFIX + "-batch-instance-role-id"
BATCH_INSTANCE_ROLE_NAME = STACK_PREFIX + "-batch-instance-role"

INSTANCE_PROFILE_ID = STACK_PREFIX + "-instance-profile-id"

# Compute Environment
COMPUTE_TYPE = "SPOT"
COMPUTE_ENVIRONMENT_ID = STACK_PREFIX + "-" + COMPUTE_TYPE.lower() + "-compute-environment-id"
COMPUTE_ENVIRONMENT_NAME = STACK_PREFIX + "-" + COMPUTE_TYPE.lower() + "-compute-environment"

# Job Queue
JOB_QUEUE_ID = STACK_PREFIX + "-job-queue-id"
JOB_QUEUE_NAME = STACK_PREFIX + "-job-queue"

# Job Definition
JOB_DEFINITION_ID = STACK_PREFIX + "-job-definition-id"
JOB_DEFINITION_NAME = STACK_PREFIX + "-job-definition"

COMPUTE_MIN_VCPUS = 0
COMPUTE_MAX_VCPUS = 4
COMPUTE_DESIRED_VCPUS = 0
COMPUTE_INSTANCE_TYPES = ["optimal"]
BID_PERCENTAGE = 90

CONTAINER_IMAGE = "AWS-ACCOUNT-ECR/processor"
CONTAINER_VCPUS = 1
CONTAINER_MEMORY = 1024

# Secret
SECRET_NAME = "dev/solar/app"


class AWSBatchStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC & Security Group
        vpc = ec2.Vpc(scope=self, id=VPC_ID, max_azs=3)

        sg = ec2.SecurityGroup(self, SECURITY_GROUP_ID, 
            vpc=vpc, 
            security_group_name=SECURITY_GROUP_NAME
        )

        # IAM Roles and Permissions
        batch_service_role = iam.Role(self, BATCH_SERVICE_ROLE_ID,
            role_name=BATCH_SERVICE_ROLE_NAME,
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBatchServiceRole")
            ]
        )

        spot_fleet_role = iam.Role(self, SPOT_FLEET_ROLE_ID,
            role_name=SPOT_FLEET_ROLE_NAME,
            assumed_by=iam.ServicePrincipal("spotfleet.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2SpotFleetTaggingRole")
            ]
        )

        batch_instance_role = iam.Role(self, BATCH_INSTANCE_ROLE_ID,
            role_name=BATCH_INSTANCE_ROLE_NAME,
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"), 
                iam.ServicePrincipal("ecs.amazonaws.com")
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role")
            ]
        )
        
        instance_profile = iam.CfnInstanceProfile(self, INSTANCE_PROFILE_ID,
            instance_profile_name=batch_instance_role.role_name,
            roles=[batch_instance_role.role_name]
        )

        # Compute Environment
        compute_environment = batch.CfnComputeEnvironment(self, COMPUTE_ENVIRONMENT_ID,
            compute_environment_name=COMPUTE_ENVIRONMENT_NAME,
            type="MANAGED",
            service_role=batch_service_role.role_arn,
            compute_resources={
                "type": COMPUTE_TYPE,
                "maxvCpus": COMPUTE_MAX_VCPUS,
                "minvCpus": COMPUTE_MIN_VCPUS,
                "desiredvCpus": COMPUTE_DESIRED_VCPUS,
                "bidPercentage": BID_PERCENTAGE,
                "spotIamFleetRole": spot_fleet_role.role_arn,
                "instanceTypes": COMPUTE_INSTANCE_TYPES,
                "instanceRole": batch_instance_role.role_name,
                "subnets": [subnet.subnet_id for subnet in vpc.public_subnets],
                "securityGroupIds": [sg.security_group_id]
            }
        )
        compute_environment.add_depends_on(instance_profile)
        
        # Job Queue
        job_queue = batch.CfnJobQueue(self, JOB_QUEUE_ID,
            job_queue_name=JOB_QUEUE_NAME,
            priority=1,
            compute_environment_order=[
                {
                    "order": 1, 
                    "computeEnvironment": compute_environment.compute_environment_name
                }
            ]
        )
        job_queue.add_depends_on(compute_environment)

        # Job Definition
        job_definition = batch.CfnJobDefinition(self, JOB_DEFINITION_ID,
            job_definition_name=JOB_DEFINITION_NAME,
            type="container",
            retry_strategy={
                "Attemps": 1
            },
            timeout={
                "AttemptDurationSeconds": 60
            },
            container_properties={
                "image": CONTAINER_IMAGE,
                "vcpus": CONTAINER_VCPUS,
                "memory": CONTAINER_MEMORY,
                "environment": [
                    {
                        "name": STACK_PREFIX + "_POSTGRES_DB",
                        "value": "{{resolve:secretsmanager:" + SECRET_NAME + ":SecretString:POSTGRES_DB}}"
                    },
                    {
                        "name": STACK_PREFIX + "_POSTGRES_USER",
                        "value": "{{resolve:secretsmanager:" + SECRET_NAME + ":SecretString:POSTGRES_USER}}"
                    }
                ]
            }
        )
