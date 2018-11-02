import boto3
from ansible_vault import Vault

#
# (c) 07/10/2018 A.Dowling
#
# create_ecs_autoscaling_group.py version 1
# boto3
# python version 2.7.14
#
# Application Auto Scaling allows you to configure automatic scaling for Amazon ECS Services
#

password = raw_input("Please enter API Key password: ")
print("you entered" + password)
vault = Vault(password)

key_data = vault.load(open('vault.yml').read())
secret_access_key = list(key_data.values())[0]
access_key_id = list(key_data.values())[1]

client = boto3.client('application-autoscaling')


scalable_target = client.register_scalable_target(
    ServiceNamespace='ecs',
    ResourceId='service/default/sample-webapp',
    ScalableDimension='ecs:service:DesiredCount',
    MinCapacity=2,
    MaxCapacity=6,
    RoleARN='string'
)

scheduled_action = client.put_scheduled_action(
    ServiceNamespace='ecs',
    Schedule='string',
    ScheduledActionName='string',
    ScalableDimension='ecs:service:DesiredCount',
    ResourceId='service/default/sample-webapp',
    StartTime=datetime(2018, 1, 1),
    EndTime=datetime(2019, 1, 1),
    ScalableTargetAction={
        'MinCapacity': 2,
        'MaxCapacity': 6
    }
)

scaling_policy_response = client.put_scaling_policy(
    PolicyName='Cloud Arch Scaling Policy',
    ServiceNamespace='ecs',
    ResourceId='service/default/sample-webapp',
    ScalableDimension='ecs:service:DesiredCount',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 50.0,
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'ECSServiceAverageCPUUtilization'
        },
        'ScaleOutCooldown': 120,
        'ScaleInCooldown': 120,
        'DisableScaleIn': False
    }
)