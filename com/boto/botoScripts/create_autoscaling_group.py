import boto3


#
# (c) 10/10/2018 A.Dowling
#
# create_autoscaling_group.py version 1
# boto3
# python version 2.7.14
#
# Creates full EC2 AutoScaling Group Architecture including the following:
#
# Sets ASG VPC details
# Creates ASG Launch Configuration
# Creates AutoScaling Group
# Enables Metric Collection on ASG
# Tags per resource created


def run_asg_script(awsvars, access_key_id, secret_access_key):
    print("Creating AutoScaling Group Architecture")

    ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    asg_client = boto3.client(
        'autoscaling',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    elb_client = boto3.client('elbv2', aws_access_key_id=access_key_id,
                              aws_secret_access_key=secret_access_key,
                              region_name=awsvars['region'])

    retrieve_vpc_details(awsvars, ec2_client, asg_client, elb_client)


def retrieve_vpc_details(awsvars, ec2_client, asg_client, elb_client):
    application_security_group = ec2_client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-name',
                'Values': [
                    awsvars['appGroupName'],
                ]
            },
        ]
    )

    print("Application Security Group is: ", application_security_group['SecurityGroups'][0]['GroupId'])

    privatesubnet1 = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['privateSubnet1Name'],
                ]
            },
        ]
    )

    print("Retrieving Private Subnet 1: " + privatesubnet1['Subnets'][0]['SubnetId'])

    privatesubnet2 = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['privateSubnet2Name'],
                ]
            },
        ]
    )

    print("Retrieving Private Subnet 2: " + privatesubnet2['Subnets'][0]['SubnetId'])

    targetgroup = elb_client.describe_target_groups(
        Names=[
            awsvars['targetGroupName'],
        ]
    )

    print("Retrieving Target Group: " + targetgroup['TargetGroups'][0]['TargetGroupArn'])
    create_autoscaling_group(awsvars, asg_client, application_security_group, targetgroup, privatesubnet1,
                             privatesubnet2)


def create_autoscaling_group(awsvars, asg_client, application_security_group, targetgroup, privatesubnet1,
                             privatesubnet2):
    user_data_script = """#!/bin/bash
    rm /var/tmp/aws-mon/instance-id"""

    launch_config = asg_client.create_launch_configuration(
        LaunchConfigurationName=awsvars['asgLaunchConfigName'],
        ImageId=awsvars['asgAMI'],
        KeyName=awsvars['keyPairName'],
        SecurityGroups=[
            application_security_group['SecurityGroups'][0]['GroupId'],
        ],
        UserData=user_data_script,
        InstanceType=awsvars['instanceType'],
        InstanceMonitoring={
            'Enabled': False
        },
        AssociatePublicIpAddress=True
    )

    print("Created Launch Config: ", launch_config)

    subnetlist = [privatesubnet1['Subnets'][0]['SubnetId'], privatesubnet2['Subnets'][0]['SubnetId']]
    print("Subnet List is: ", subnetlist)

    auto_scaling_group = asg_client.create_auto_scaling_group(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        LaunchConfigurationName=awsvars['asgLaunchConfigName'],
        MinSize=awsvars['asgMinSize'],
        MaxSize=awsvars['asgMaxSize'],
        DesiredCapacity=awsvars['asgDesiredSize'],
        DefaultCooldown=awsvars['asgCoolDown'],
        AvailabilityZones=[
            awsvars['azZone1'], awsvars['azZone2'],
        ],
        TargetGroupARNs=[
            targetgroup['TargetGroups'][0]['TargetGroupArn'],
        ],
        HealthCheckType=awsvars['asgHealthCheckType'],
        HealthCheckGracePeriod=awsvars['asgCoolDown'],
        VPCZoneIdentifier=', '.join(map(str, subnetlist)),
        TerminationPolicies=[
            awsvars['asgTerminationPolicies'],
        ],
        NewInstancesProtectedFromScaleIn=True,
        Tags=[
            {
                'ResourceId': awsvars['autoScalingGroupName'],
                'ResourceType': 'auto-scaling-group',
                'Key': 'Name',
                'Value': awsvars['autoScalingGroupTag'],
                'PropagateAtLaunch': True
            },
        ]
    )

    print("Created AutoScaling Group: ", auto_scaling_group)

    asg_client.enable_metrics_collection(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        Metrics=[
            'GroupMinSize',
            'GroupDesiredCapacity',
            'GroupMaxSize',
            'GroupPendingInstances',
            'GroupTerminatingInstances',
            'GroupTotalInstances'
        ],
        Granularity='1Minute'
    )
