import boto3


#
# (c) 07/10/2018 A.Dowling
#
# create_vpc.py version 1
# boto3
# python version 2.7.14
#
# Creates full VPC architecture including the following:
# A VPC
# Internet Gateway
# Associated Public and Private Subnets
# Public and Private Route Tables
# Application, RDS and Application Load Balancer Security Groups
# Associated Security Group Rules
# Tags per resource created

def run_vpc_script(awsvars, access_key_id, secret_access_key):
    ec2 = boto3.resource('ec2', aws_access_key_id=access_key_id,
                         aws_secret_access_key=secret_access_key,
                         region_name=awsvars['region'])

    ec2client = boto3.client('ec2', aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=awsvars['region'])

    create_vpc(awsvars, ec2, ec2client)


def create_vpc(awsvars, ec2, ec2client):
    # Create and tag the VPC
    vpc = ec2.create_vpc(CidrBlock=awsvars['vpcCidrBlock'])
    vpc.wait_until_available()
    print("Creating VPC with id: " + vpc.id)

    # Enable DNS Hostnames in the VPC
    vpc.modify_attribute(EnableDnsSupport={'Value': True})
    vpc.modify_attribute(EnableDnsHostnames={'Value': True})
    print("Enabling DNS for VPC: " + vpc.id)

    # Create, tag, then attach an internet gateway to the VPC
    internet_gateway = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
    print("Creating Internet Gateway with id: " + internet_gateway.id)

    # create elastic ip for use with nat gateway
    eip = ec2client.allocate_address(
        Domain='vpc'
    )
    print("Created Elastic IP: ", eip)

    # Create a Public Route Table
    public_route_table = vpc.create_route_table()
    print("Creating Public Route Table with id: " + public_route_table.id)

    # Create a route for internet traffic to from the public route table
    public_route_table.create_route(
        RouteTableId=public_route_table.id,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=internet_gateway.id
    )
    print("Creating Route Table public routing rule")

    # Create Public Subnet 1
    public_subnet1 = ec2.create_subnet(
        CidrBlock=awsvars['publicSubnet1CidrBlock'],
        VpcId=vpc.id,
        AvailabilityZone=awsvars['availabilityZone1']
    )
    print("Creating Public Subnet 1 with id: " + public_subnet1.id)

    ec2client.modify_subnet_attribute(
        MapPublicIpOnLaunch={
            'Value': True
        },
        SubnetId=public_subnet1.id
    )

    # Create Public Subnet 2
    public_subnet2 = ec2.create_subnet(
        CidrBlock=awsvars['publicSubnet2CidrBlock'],
        VpcId=vpc.id,
        AvailabilityZone=awsvars['availabilityZone2']
    )
    print("Creating Public Subnet 2 with id: " + public_subnet2.id)

    ec2client.modify_subnet_attribute(
        MapPublicIpOnLaunch={
            'Value': True
        },
        SubnetId=public_subnet2.id
    )

    # Associate the Public Route Table with the Subnets
    public_route_table.associate_with_subnet(SubnetId=public_subnet1.id)
    public_route_table.associate_with_subnet(SubnetId=public_subnet2.id)

    nat = ec2client.create_nat_gateway(
        AllocationId=eip['AllocationId'],
        SubnetId=public_subnet1.id
    )
    print("Waiting for NAT Gateway creation . . . ")
    waiter = ec2client.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds=[
        nat['NatGateway']['NatGatewayId']
    ], )
    print("Nat Gateway created in Public Subnet 1: ", nat)

    # Create a Private Route Table
    private_route_table = ec2.create_route_table(VpcId=vpc.id)
    print("Creating Private Route Table with id: " + private_route_table.id)

    # Create Private Subnet 1
    private_subnet1 = ec2.create_subnet(
        CidrBlock=awsvars['privateSubnet1CidrBlock'],
        VpcId=vpc.id,
        AvailabilityZone=awsvars['availabilityZone1']
    )
    print("Creating Private Subnet 1 with id: " + private_subnet1.id)

    # Create Private Subnet 2
    private_subnet2 = ec2.create_subnet(
        CidrBlock=awsvars['privateSubnet2CidrBlock'],
        VpcId=vpc.id,
        AvailabilityZone=awsvars['availabilityZone2'])
    print("Creating Private Subnet 2 with id: " + private_subnet2.id)

    # Associate the Private Route Table with the Subnets
    private_route_table.associate_with_subnet(SubnetId=private_subnet1.id)
    private_route_table.associate_with_subnet(SubnetId=private_subnet2.id)

    # Associate the Private Route Table with the NatGateway to allow outbound traffic to the internet
    private_route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        NatGatewayId=nat['NatGateway']['NatGatewayId']
    )

    # Creating Resource Tags
    vpc.create_tags(Tags=[{"Key": "Name", "Value": awsvars['vpcName']}])
    internet_gateway.create_tags(Tags=[{"Key": "Name", "Value": awsvars['igName']}])
    public_subnet1.create_tags(Tags=[{"Key": "Name", "Value": awsvars['publicSubnet1Name']}])
    public_subnet2.create_tags(Tags=[{"Key": "Name", "Value": awsvars['publicSubnet2Name']}])
    private_subnet1.create_tags(Tags=[{"Key": "Name", "Value": awsvars['privateSubnet1Name']}])
    private_subnet2.create_tags(Tags=[{"Key": "Name", "Value": awsvars['privateSubnet2Name']}])
    public_route_table.create_tags(Tags=[{"Key": "Name", "Value": awsvars['publicRouteTable']}])
    private_route_table.create_tags(Tags=[{"Key": "Name", "Value": awsvars['privateRouteTable']}])

    ec2client.create_tags(
        Resources=[
            eip['AllocationId'],
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': awsvars['eipName']
            },
        ]
    )
    ec2client.create_tags(
        Resources=[
            nat['NatGateway']['NatGatewayId'],
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': awsvars['natGatewayName']
            },
        ]
    )

    create_security_groups(awsvars, vpc, ec2, ec2client)


def create_security_groups(awsvars, vpc, ec2, ec2client):
    # Create Application Tier Security Group
    application_sec_group = ec2.create_security_group(
        DryRun=False, GroupName=awsvars['appGroupName'], Description=awsvars['applicationSecurityGroupName'],
        VpcId=vpc.id)
    print("Creating VPC Public Security Group with id: " + application_sec_group.id)

    # Create Web Tier Security Group
    alb_sec_group = ec2.create_security_group(
        DryRun=False, GroupName=awsvars['albGroupName'], Description=awsvars['albSecurityGroupName'], VpcId=vpc.id)
    print("Creating VPC ALB Security Group with id: " + alb_sec_group.id)

    # Create RDS Security Group
    rds_sec_group = ec2.create_security_group(
        DryRun=False, GroupName=awsvars['rdsGroupName'], Description=awsvars['rdsSecurityGroupName'], VpcId=vpc.id)
    print("Creating VPC RDS Security Group with id: " + rds_sec_group.id)

    application_sec_group.create_tags(Tags=[{"Key": "Name", "Value": awsvars['applicationSecurityGroupName']}])
    alb_sec_group.create_tags(Tags=[{"Key": "Name", "Value": awsvars['albSecurityGroupName']}])
    rds_sec_group.create_tags(Tags=[{"Key": "Name", "Value": awsvars['rdsSecurityGroupName']}])

    print("Creating Security Group Rules")

    ec2client.authorize_security_group_ingress(GroupId=alb_sec_group.id,
                                               IpProtocol='tcp',
                                               FromPort=80,
                                               ToPort=80,
                                               CidrIp='0.0.0.0/0'
                                               )

    ec2client.authorize_security_group_ingress(GroupId=alb_sec_group.id,
                                               IpProtocol='tcp',
                                               FromPort=443,
                                               ToPort=443,
                                               CidrIp='0.0.0.0/0'
                                               )

    ec2client.authorize_security_group_ingress(GroupId=alb_sec_group.id,
                                               IpProtocol='tcp',
                                               FromPort=22,
                                               ToPort=22,
                                               CidrIp=awsvars['sshCidrBlock1']
                                               )

    ec2client.authorize_security_group_ingress(GroupId=alb_sec_group.id,
                                               IpProtocol='tcp',
                                               FromPort=22,
                                               ToPort=22,
                                               CidrIp=awsvars['sshCidrBlock2']
                                               )

    ec2client.authorize_security_group_ingress(GroupId=alb_sec_group.id,
                                               IpProtocol='tcp',
                                               FromPort=22,
                                               ToPort=22,
                                               CidrIp=awsvars['sshCidrBlock3']
                                               )

    # Allow Application Security Group to receive traffic from ALB Security group
    ec2client.authorize_security_group_ingress(GroupId=application_sec_group.id,
                                               IpPermissions=[{'IpProtocol': 'tcp',
                                                               'FromPort': 80,
                                                               'ToPort': 80,
                                                               'UserIdGroupPairs': [{'GroupId': alb_sec_group.id}]
                                                               }]
                                               )

    ec2client.authorize_security_group_ingress(GroupId=application_sec_group.id,
                                               IpPermissions=[{'IpProtocol': 'tcp',
                                                               'FromPort': 22,
                                                               'ToPort': 22,
                                                               'UserIdGroupPairs': [{'GroupId': alb_sec_group.id}]
                                                               }]
                                               )
    # Allow RDS Security Group to receive traffic from Application Security group on 3306
    ec2client.authorize_security_group_ingress(GroupId=rds_sec_group.id,
                                               IpPermissions=[{'IpProtocol': 'tcp',
                                                               'FromPort': 3306,
                                                               'ToPort': 3306,
                                                               'UserIdGroupPairs': [
                                                                   {'GroupId': application_sec_group.id}]
                                                               }]
                                               )

    print("Finished VPC Architecture Creation for: " + vpc.id)
