import boto3


#
# (c) 29/10/2018 A.Dowling
#
# create_ec2_instance.py version 1
# boto3
# python version 2.7.14
#
# Creates an EC2 instance in a public subnet including the following actions:
#
# Retrieves VPC details
# Creates EC2 instance in public subnet with specified parameters.
# Tags per resource created


def run_ec2_script(awsvars, access_key_id, secret_access_key):
    ec2 = boto3.resource(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    alb_security_group = ec2_client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-name',
                'Values': [
                    awsvars['albGroupName'],
                ]
            },
        ]
    )

    print("Security Group is: ", alb_security_group['SecurityGroups'][0]['GroupId'])

    publicsubnet1 = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['publicSubnet1Name'],
                ]
            },
        ]
    )

    print("Retrieving Public Subnet 1: " + publicsubnet1['Subnets'][0]['SubnetId'])
    create_ec2_instance(awsvars, ec2, alb_security_group, publicsubnet1)


def create_ec2_instance(awsvars, ec2, alb_security_group, publicsubnet1):
    instance = ec2.create_instances(
        ImageId=awsvars['publicServerAMI'],
        InstanceType=awsvars['instanceType'],
        KeyName=awsvars['keyPairName'],
        MaxCount=awsvars['ec2Count'],
        MinCount=awsvars['ec2Count'],
        Monitoring={
            'Enabled': False
        },
        SecurityGroupIds=[
            alb_security_group['SecurityGroups'][0]['GroupId'],
        ],
        SubnetId=publicsubnet1['Subnets'][0]['SubnetId'],
        EbsOptimized=False,
        TagSpecifications=[
            {
                'ResourceType': awsvars['targetType'],
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': awsvars['publicServerName']
                    },
                ]
            },
        ]
    )
    print("Created ec2 Instance with the following parameters: ", instance)
