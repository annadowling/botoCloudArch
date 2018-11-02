import boto3
from ansible_vault import Vault

#
# (c) 07/10/2018 A.Dowling
#
# deploy_ecs_container.py version 1
# boto3
# python version 2.7.14
#
region = 'eu-west-1'

password = raw_input("Please enter API Key password: ")
print("you entered" + password)
vault = Vault(password)

key_data = vault.load(open('vault.yml').read())
secret_access_key = list(key_data.values())[0]
access_key_id = list(key_data.values())[1]

# ECS Details
cluster_name = "CloudArchitect"
service_name = "service_cloud_architect"
task_name = "cloud_architect"

# Let's use Amazon ECS
ecs_client = boto3.client(
    'ecs',
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name=region
)

# Let's use Amazon EC2
ec2_client = boto3.client(
    'ec2',
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name=region
)

public_security_group = ec2_client.describe_security_groups(
    Filters=[
        {
            'Name': 'group-name',
            'Values': [
                'vpc_public_sg',
            ]
        },
    ]
)

print("Security Group is: ", public_security_group['SecurityGroups'][0]['GroupId'])

publicSubnet1 = ec2_client.describe_subnets(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Public Subnet 1',
            ]
        },
    ]
)

print("Retrieving Public Subnet 1: " + publicSubnet1['Subnets'][0]['SubnetId'])

cluster_response = ecs_client.create_cluster(
    clusterName=cluster_name
)

print(cluster_response)

# Create EC2 instance(s) in the cluster
# By default, container instance launches into default cluster.


# TODO review this, looks incorrect for IamInstanceProfile section.
client_instances_response = ec2_client.run_instances(
    # Use the official ECS image
    ImageId="ami-05b65c0f6a75c1c64",
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'Cloud Arch Docker instance'
                },
            ]
        },
    ],
    SecurityGroups=public_security_group['SecurityGroups'][0]['GroupId'],
    SubnetId=publicSubnet1['Subnets'][0]['SubnetId'],
    UserData="#!/bin/bash \n echo ECS_CLUSTER=" + cluster_name + " >> /etc/ecs/ecs.config",
    KeyName='/Users/annadowling/Desktop/exercisesKeyPair.pem'
)

print(client_instances_response)

# Create a task definition
register_task_definition_response = ecs_client.register_task_definition(
    networkMode='awsvpc',
    containerDefinitions=[
        {
            "name": "cloud-architecture",
            "links": [
                "mysql"
            ],
            "image": "cloud-architecture",
            "essential": True,
            "portMappings": [
                {
                    "containerPort": 8080,
                    "hostPort": 8080
                }
            ],
            "memory": 300,
            "cpu": 10
        },
        {
            "environment": [
                {
                    "name": "MYSQL_USER",
                    "value": "root"
                },
                {
                    "name": "MYSQL_PORT",
                    "value": "3306"
                },
                {
                    "name": "MYSQL_DATABASE",
                    "value": "aws"
                },
                {
                    "name": "MYSQL_ROOT_PASSWORD",
                    "value": "ozzrules"
                },
                {
                    "name": "MYSQL_HOST",
                    "value": "docker-mysql"
                }
            ],
            "name": "docker-mysql",
            "image": "mysql",
            "cpu": 10,
            "memory": 300,
            "essential": True
        }
    ],
    family="cloud_architect",
)

print(register_task_definition_response)

# Create service with exactly 1 desired instance of the task
# Info: Amazon ECS allows you to run and maintain a specified number
# (the "desired count") of instances of a task definition
# simultaneously in an ECS cluster.

create_service_response = ecs_client.create_service(
    cluster=cluster_name,
    serviceName=service_name,
    taskDefinition=task_name,
    loadBalancers=[
        {
            'targetGroupArn': 'string',
            'loadBalancerName': 'string',
            'containerName': 'string',
            'containerPort': 8080
        },
    ],
    desiredCount=1,
    clientToken='request_identifier_string',
    deploymentConfiguration={
        'maximumPercent': 200,
        'minimumHealthyPercent': 50
    }
)

print(create_service_response)
