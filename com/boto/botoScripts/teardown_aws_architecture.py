import boto3


#
# (c) 29/10/2018 A.Dowling
#
# teardown_aws_architecture.py version 1
# boto3
# python version 2.7.14
#
# Deletes all previously created AWS Architecture Components from specified parameters including:
#
# Deletion of all ec2 instances
# Deletion of RDS instance
# Deletion of AutoScaling group
# Deletion of CloudWatch alarms and Scaling Policies
# Deletion of SNS topics
# Deletion of Load Balancer
# Deletion of Security Groups
# Deletion of Internet Gateway
# Deletion of Subnets
# Deletion of Route Tables
# Deletion of VPC

def delete_rds(awsvars, rds):
    db_response = rds.delete_db_instance(
        DBInstanceIdentifier=awsvars['rdsDBId'],
        SkipFinalSnapshot=True
    )
    print("Waiting for RDS Instance Deletion . . .")
    waiter = rds.get_waiter('db_instance_deleted')
    waiter.wait(
        DBInstanceIdentifier=awsvars['rdsDBId'],
    )

    print("Deleted RDS Instance: ", db_response)


def delete_rds_subnet(awsvars, rds):
    sg_response = rds.delete_db_subnet_group(
        DBSubnetGroupName=awsvars['rdsSubnetGroupName']
    )

    print("Deleted DB Subnet Group: ", sg_response)


def delete_instances(ec2, ec2_client):
    # Retrieve running instances
    running_instances = ec2.instances.filter(Filters=[{
        'Name': 'instance-state-name',
        'Values': ['running']}])

    for instance in running_instances:
        ec2_response = ec2_client.terminate_instances(
            InstanceIds=[
                instance.id,
            ],
            DryRun=False
        )
        print("Waiting for Instance Termination . . . ")
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(
            InstanceIds=[
                instance.id,
            ],
        )
        print("Deleted Instance: ", ec2_response)


def delete_autoscaling_group(awsvars, asg_client):
    cpu_policy_response = asg_client.delete_policy(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        PolicyName=awsvars['scaleOutPolicyNameCPU']
    )
    print("Deleted CPU Policy: ", cpu_policy_response)

    sc_policy_response = asg_client.delete_policy(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        PolicyName=awsvars['scaleOutPolicyNameSC']
    )
    print("Deleted Status Check Policy: ", sc_policy_response)

    asg_response = asg_client.delete_auto_scaling_group(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        ForceDelete=True
    )

    print("Deleted AutoScaling Group: ", asg_response)


def delete_cloudwatch_alarms(awsvars, cw_client):
    cw_response = cw_client.delete_alarms(
        AlarmNames=[
            awsvars['statusCheckAlarmName'],
            awsvars['cpuAlarmName']
        ]
    )
    print("Deleted Cloudwatch Alarms: ", cw_response)


def delete_alb(awsvars, elbclient):
    alb = elbclient.describe_load_balancers(
        Names=[
            awsvars['albName'],
        ]
    )

    print("Load Balancer Is: " + alb['LoadBalancers'][0]['LoadBalancerArn'])

    listener = elbclient.describe_listeners(
        LoadBalancerArn=alb['LoadBalancers'][0]['LoadBalancerArn'],
    )

    rule = elbclient.describe_rules(
        ListenerArn=listener['Listeners'][0]['ListenerArn'],
    )

    rule_response = elbclient.delete_rule(
        RuleArn=rule['Rules'][0]['RuleArn']
    )
    print("Deleted Load Balancer Rule: ", rule_response)

    listener_response = elbclient.delete_listener(
        ListenerArn=listener['Listeners'][0]['ListenerArn']
    )
    print("Deleted Load Balancer Listener: ", listener_response)

    alb_response = elbclient.delete_load_balancer(
        LoadBalancerArn=alb['LoadBalancers'][0]['LoadBalancerArn']
    )

    print("Waiting for Load Balancer Deletion . . .")
    waiter = elbclient.get_waiter('load_balancers_deleted')
    waiter.wait(
        LoadBalancerArns=[
            alb['LoadBalancers'][0]['LoadBalancerArn'],
        ],
    )

    print("Deleted Load Balancer: ", alb_response)


def delete_launch_config(awsvars, asg_client):
    lc_response = asg_client.delete_launch_configuration(
        LaunchConfigurationName=awsvars['asgLaunchConfigName']
    )
    print("Deleted Launch Configuration: ", lc_response)


def delete_targetgroup(awsvars, elbclient):
    targetgroup = elbclient.describe_target_groups(
        Names=[
            awsvars['targetGroupName'],
        ]
    )

    tg_response = elbclient.delete_target_group(
        TargetGroupArn=targetgroup['TargetGroups'][0]['TargetGroupArn']
    )
    print("Deleted Target Group: ", tg_response)


def delete_internet_gateway(igname, awsvars, ec2_client):
    gateway = ec2_client.describe_internet_gateways(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    igname,
                ]
            },
        ],
        DryRun=False,
    )

    vpc = ec2_client.describe_vpcs(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['vpcName'],
                ]
            },
        ]
    )

    detach = ec2_client.detach_internet_gateway(
        DryRun=False,
        InternetGatewayId=gateway['InternetGateways'][0]['InternetGatewayId'],
        VpcId=vpc['Vpcs'][0]['VpcId']
    )
    print("Detached Internet Gateway: ", detach)

    gateway_response = ec2_client.delete_internet_gateway(
        DryRun=False,
        InternetGatewayId=gateway['InternetGateways'][0]['InternetGatewayId']
    )
    print("Deleted Internet Gateway: ", gateway_response)


def delete_security_groups(name, ec2_client):
    sg = ec2_client.describe_security_groups(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    name,
                ]
            },
        ]
    )

    print('Security Group to delete is: ', sg)

    sg_response = ec2_client.delete_security_group(
        GroupId=sg['SecurityGroups'][0]['GroupId'],
        DryRun=False
    )

    print("Deleted Security Group: ", sg_response)


def delete_subnet(name, ec2_client):
    subnet = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    name,
                ]
            },
        ],
        DryRun=False
    )

    subnet_response = ec2_client.delete_subnet(
        SubnetId=subnet['Subnets'][0]['SubnetId'],
        DryRun=False
    )
    print("Deleted Subnet: ", subnet_response)


def delete_route_table(name, ec2_client):
    route_table = ec2_client.describe_route_tables(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    name,
                ]
            },
        ],
        DryRun=False
    )
    print('Association: ', route_table['RouteTables'][0]['Associations'])

    for subnet in route_table['RouteTables'][0]['Associations']:
        ec2_client.disassociate_route_table(
            AssociationId=subnet['RouteTableAssociationId']
        )

    rt_response = ec2_client.delete_route_table(
        DryRun=False,
        RouteTableId=route_table['RouteTables'][0]['RouteTableId']
    )
    print("Deleted RouteTable: ", rt_response)


def delete_nat_gateway(awsvars, ec2_client):
    nat = ec2_client.describe_nat_gateways(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['natGatewayName'],
                ]
            },
        ]
    )

    nat_response = ec2_client.delete_nat_gateway(
        NatGatewayId=nat['NatGateways'][0]['NatGatewayId']
    )
    print("Deleted NAT: ", nat_response)


def delete_elastic_ip(awsvars, ec2_client):
    eip = ec2_client.describe_addresses(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['eipName'],
                ]
            },
        ]
    )
    print('eip is: ', eip)

    eip_response = ec2_client.release_address(
        AllocationId=eip['Addresses'][0]['AllocationId']
    )
    print("Deleted Elastic IP: ", eip_response)


def delete_vpc(awsvars, ec2_client):
    vpc = ec2_client.describe_vpcs(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    awsvars['vpcName'],
                ]
            },
        ]
    )

    vpc_response = ec2_client.delete_vpc(
        VpcId=vpc['Vpcs'][0]['VpcId'],
        DryRun=False
    )

    print("Deleted VPC: ", vpc_response)


def run_delete_script(awsvars, access_key_id, secret_access_key):
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

    asg_client = boto3.client(
        'autoscaling',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    rds = boto3.client(
        'rds',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    cw_client = boto3.client('cloudwatch',
                             aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=awsvars['region']
                             )

    sns_client = boto3.client(
        'sns',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    elbclient = boto3.client('elbv2', aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=awsvars['region'])

    delete_autoscaling_group(awsvars, asg_client)
    delete_rds(awsvars, rds)
    delete_rds_subnet(awsvars, rds)
    delete_instances(ec2, ec2_client)
    delete_cloudwatch_alarms(awsvars, cw_client)
    delete_alb(awsvars, elbclient)
    delete_launch_config(awsvars, asg_client)
    delete_targetgroup(awsvars, elbclient)
    delete_security_groups(awsvars['rdsSecurityGroupName'], ec2_client)
    delete_security_groups(awsvars['applicationSecurityGroupName'], ec2_client)
    delete_route_table(awsvars['publicRouteTable'], ec2_client)
    delete_route_table(awsvars['privateRouteTable'], ec2_client)
    delete_nat_gateway(awsvars, ec2_client)
    delete_subnet(awsvars['publicSubnet2Name'], ec2_client)
    delete_subnet(awsvars['privateSubnet1Name'], ec2_client)
    delete_subnet(awsvars['privateSubnet2Name'], ec2_client)
    delete_internet_gateway(awsvars['igName'], awsvars, ec2_client)
    delete_security_groups(awsvars['albSecurityGroupName'], ec2_client)
    delete_elastic_ip(awsvars, ec2_client)
    delete_subnet(awsvars['publicSubnet1Name'], ec2_client)
    delete_vpc(awsvars, ec2_client)
