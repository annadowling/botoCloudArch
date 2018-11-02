import boto3

#
# (c) 10/10/2018 A.Dowling
#
# create_alb.py version 1
# boto3
# python version 2.7.14
#
# Creates full Application Load Balancer Architecture including the following:
#
# Application Load Balancer Creation
# Target Group Creation
# Enables sticky sessions on load balancer
# Load Balancer Listener and Listener Forwarding Rules creation
# Tags per resource created


def run_alb_script(awsvars, access_key_id, secret_access_key):
    print("Creating Application Load Balancer Architecture")

    elbclient = boto3.client('elbv2', aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=awsvars['region'])

    ec2client = boto3.client('ec2', aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=awsvars['region'])

    create_alb(awsvars, elbclient, ec2client)


def create_alb(awsvars, elbclient, ec2client):
    alb_security_group = ec2client.describe_security_groups(
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

    publicsubnet1 = ec2client.describe_subnets(
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

    publicsubnet2 = ec2client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['publicSubnet2Name'],
                ]
            },
        ]
    )

    print("Retrieving Public Subnet 2: " + publicsubnet2['Subnets'][0]['SubnetId'])

    alb = elbclient.create_load_balancer(
        Name=awsvars['albName'],
        Subnets=[
            publicsubnet1['Subnets'][0]['SubnetId'],
            publicsubnet2['Subnets'][0]['SubnetId']
        ],
        SecurityGroups=[
            alb_security_group['SecurityGroups'][0]['GroupId']
        ],
        Scheme=awsvars['scheme'],
        Tags=[
            {
                'Key': 'Name',
                'Value': awsvars['albTag']
            },
        ],
        Type=awsvars['lbType'],
        IpAddressType=awsvars['ipAddressType']
    )

    print("Created Load Balancer: " + alb['LoadBalancers'][0]['LoadBalancerArn'])
    create_targetgroup(awsvars, elbclient, alb)


def create_targetgroup(awsvars, elbclient, alb):
    targetgroup = elbclient.create_target_group(
        Name=awsvars['targetGroupName'],
        Protocol=awsvars['protocol'],
        Port=awsvars['port'],
        VpcId=alb['LoadBalancers'][0]['VpcId'],
        HealthCheckProtocol=awsvars['protocol'],
        HealthCheckPort=awsvars['httpPort'],
        HealthCheckPath=awsvars['pathPattern'],
        HealthCheckIntervalSeconds=awsvars['healthCheckIntervalSeconds'],
        HealthCheckTimeoutSeconds=awsvars['healthCheckTimeoutSeconds'],
        HealthyThresholdCount=awsvars['healthyThresholdCount'],
        UnhealthyThresholdCount=awsvars['unhealthyThresholdCount'],
        Matcher={
            'HttpCode': awsvars['httpCode']
        },
        TargetType=awsvars['targetType']
    )

    print("Created Target Group: " + targetgroup['TargetGroups'][0]['TargetGroupArn'])

    elbclient.modify_target_group_attributes(
        TargetGroupArn=targetgroup['TargetGroups'][0]['TargetGroupArn'],
        Attributes=[
            {
                'Key': 'stickiness.enabled',
                'Value': awsvars['stickinessEnabled'],
            },
            {
                'Key': 'deregistration_delay.timeout_seconds',
                'Value': awsvars['deregistrationDelay'],
            },
            {
                'Key': 'stickiness.type',
                'Value': awsvars['stickinessType'],
            },
            {
                'Key': 'stickiness.lb_cookie.duration_seconds',
                'Value': awsvars['stickinessDuration'],
            },
        ]
    )

    print("Added sticky session details to target group: " + targetgroup['TargetGroups'][0]['TargetGroupArn'])
    create_lb_listener(awsvars, elbclient, targetgroup, alb)


def create_lb_listener(awsvars, elbclient, targetgroup, alb):
    listener = elbclient.create_listener(
        DefaultActions=[
            {
                'TargetGroupArn': targetgroup['TargetGroups'][0]['TargetGroupArn'],
                'Type': 'forward',
            },
        ],
        LoadBalancerArn=alb['LoadBalancers'][0]['LoadBalancerArn'],
        Port=awsvars['port'],
        Protocol=awsvars['protocol'],
    )

    print("Created Listener: " + listener['Listeners'][0]['ListenerArn'])

    listenerrule = elbclient.create_rule(
        Actions=[
            {
                'TargetGroupArn': targetgroup['TargetGroups'][0]['TargetGroupArn'],
                'Type': awsvars['listenerType'],
            },
        ],
        Conditions=[
            {
                'Field': awsvars['forwardType'],
                'Values': [
                    awsvars['pathPattern'],
                ],
            },
        ],
        ListenerArn=listener['Listeners'][0]['ListenerArn'],
        Priority=1,
    )

    print("Created Listener Rule: ", listenerrule['Rules'][0]['RuleArn'])
