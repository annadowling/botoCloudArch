import boto3
import time


#
# (c) 10/10/2018 A.Dowling
#
# create_rds.py version 1
# boto3
# python version 2.7.14
#
# Creates a Privately available RDS Instance for use with application architecture inside VPC:
#
# Retrieves VPC details
# Creates RDS DB Subnet Group.
# Creates RDS Instance.
# Tags per resource created
# Waits for RDS instance to become available(via status check) before script can finish.


def run_rds_script(awsvars, access_key_id, secret_access_key):
    print("Creating RDS Instance")

    ec2_client = boto3.client(
        'ec2',
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

    db_security_group = ec2_client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-name',
                'Values': [
                    awsvars['rdsGroupName'],
                ]
            },
        ]
    )

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
    create_db_subnet(awsvars, rds, db_security_group, privatesubnet1, privatesubnet2)


def create_db_subnet(awsvars, rds, db_security_group, privatesubnet1, privatesubnet2):
    db_subnet_group = rds.create_db_subnet_group(
        DBSubnetGroupName=awsvars['rdsSubnetGroupName'],
        DBSubnetGroupDescription=awsvars['subnetGroupDesc'],
        SubnetIds=[
            privatesubnet1['Subnets'][0]['SubnetId'],
            privatesubnet2['Subnets'][0]['SubnetId']
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': awsvars['rdsSubnetGroupName']
            },
        ]
    )
    print("Created RDS DB Subnet Group", db_subnet_group)
    create_rds_instance(awsvars, rds, db_security_group)


def create_rds_instance(awsvars, rds, db_security_group):
    rds.create_db_instance(
        DBSubnetGroupName=awsvars['rdsSubnetGroupName'],
        DBInstanceIdentifier=awsvars['rdsDBId'],
        AllocatedStorage=awsvars['rdsStorage'],
        DBName=awsvars['rdsDBName'],
        Engine=awsvars['rdsEngine'],
        StorageType=awsvars['rdsStorageType'],
        AutoMinorVersionUpgrade=True,
        MultiAZ=True,
        MasterUsername=awsvars['rdsMasterUser'],
        MasterUserPassword=awsvars['rdsMasterPassword'],
        VpcSecurityGroupIds=[db_security_group['SecurityGroups'][0]['GroupId']],
        PubliclyAccessible=False,
        DBInstanceClass=awsvars['rdsInstanceClass'],
        Tags=[
            {
                'Key': 'Name',
                'Value': awsvars['rdsDBId']
            },
        ], )
    print("Starting RDS instance ")

    running = True
    while running:
        response = rds.describe_db_instances(DBInstanceIdentifier=awsvars['rdsDBId'])

        db_instances = response['DBInstances']
        if len(db_instances) != 1:
            raise Exception('More than one DB instance returned; this should never happen')

        db_instance = db_instances[0]

        status = db_instance['DBInstanceStatus']

        print("Last DB status: %s" % status)

        time.sleep(5)
        if status == 'available':
            endpoint = db_instance['Endpoint']
            host = endpoint['Address']

            print("DB instance ready with host: %s" % host)
            running = False
