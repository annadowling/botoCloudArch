import boto3


#
# (c) 18/10/2018 A.Dowling
#
# create_cloudwatch_monitoring.py version 1
# boto3
# python version 2.7.14
#
# Creates CloudWatch Alarm Monitoring for specified metrics including the following:
#
# Creates ASG Scaling Policies for use with CloudWatch Metric Types
# Creates the CloudWatch Alarms (High CPU and Instance StatusCheckFailure)
# Tags per resource created

def run_cloudwatch_script(awsvars, access_key_id, secret_access_key):
    print("Creating CloudWatch Monitoring for AutoScaling Group")

    asg_client = boto3.client(
        'autoscaling',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=awsvars['region']
    )

    cw_client = boto3.client('cloudwatch',
                             aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=awsvars['region']
                             )
    create_scaling_policies(awsvars, asg_client, cw_client)


def create_scaling_policies(awsvars, asg_client, cw_client):
    status_check_scale_out_policy = asg_client.put_scaling_policy(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        PolicyName=awsvars['scaleOutPolicyNameSC'],
        PolicyType=awsvars['scalingPolicyType'],
        AdjustmentType=awsvars['adjustmentType'],
        ScalingAdjustment=awsvars['adjustmentCount'],
        Cooldown=awsvars['scalingCoolDown']
    )

    print("Created Status Check AutoScaling Policy for Scale Out: ", status_check_scale_out_policy)

    status_check_scaling_policy_scale_in = asg_client.put_scaling_policy(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        PolicyName=awsvars['scaleInPolicyNameSC'],
        PolicyType=awsvars['scalingPolicyType'],
        AdjustmentType=awsvars['adjustmentType'],
        ScalingAdjustment=awsvars['scaleInAdjustment'],
        Cooldown=awsvars['scalingCoolDown']
    )

    print("Created Status Check AutoScaling Policy for Scale In: ", status_check_scaling_policy_scale_in)

    cpu_scale_out_policy = asg_client.put_scaling_policy(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        PolicyName=awsvars['scaleOutPolicyNameCPU'],
        PolicyType=awsvars['scalingPolicyType'],
        AdjustmentType=awsvars['adjustmentType'],
        ScalingAdjustment=awsvars['adjustmentCount'],
        Cooldown=awsvars['scalingCoolDown']
    )
    print("Created CPU AutoScaling Policy for Scale Out: ", status_check_scale_out_policy)

    cpu_scale_in_policy = asg_client.put_scaling_policy(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        PolicyName=awsvars['scaleInPolicyNameCPU'],
        PolicyType=awsvars['scalingPolicyType'],
        AdjustmentType=awsvars['adjustmentType'],
        ScalingAdjustment=awsvars['scaleInAdjustment'],
        Cooldown=awsvars['scalingCoolDown']
    )
    print("Created CPU AutoScaling Policy for Scale In: ", cpu_scale_in_policy)

    create_cloudwatch_alarms(awsvars, cw_client, status_check_scale_out_policy, status_check_scaling_policy_scale_in,
                             cpu_scale_out_policy, cpu_scale_in_policy)


def create_cloudwatch_alarms(awsvars, cw_client, status_check_scale_out_policy, status_check_scaling_policy_scale_in,
                             cpu_scale_out_policy, cpu_scale_in_policy):
    # Create CloudWatch StatusCheckFailed scale out alarm
    status_check_failed_alarm = cw_client.put_metric_alarm(
        AlarmName=awsvars['statusCheckAlarmName'],
        ComparisonOperator=awsvars['operator'],
        EvaluationPeriods=awsvars['evaluationPeriods'],
        MetricName=awsvars['statusCheckMetric'],
        Namespace=awsvars['nameSpace'],
        Period=awsvars['period'],
        Statistic=awsvars['scStatistic'],
        Threshold=awsvars['scThreshold'],
        ActionsEnabled=True,
        AlarmActions=[
            status_check_scale_out_policy['PolicyARN']
        ],
        OKActions=[
            status_check_scaling_policy_scale_in['PolicyARN']
        ],
        Dimensions=[
            {
                'Name': 'AutoScalingGroupName',
                'Value': awsvars['autoScalingGroupName']
            },
        ],
        AlarmDescription=awsvars['scFailDescription'],
        Unit=awsvars['scUnit']
    )

    print("Created Status Check Failed CloudWatch Alarm with parameters: ", status_check_failed_alarm)

    # Create CloudWatch Web_Server_CPU_Utilization high alarm
    high_cpu_alarm = cw_client.put_metric_alarm(
        AlarmName=awsvars['cpuAlarmName'],
        ComparisonOperator=awsvars['operator'],
        EvaluationPeriods=awsvars['evaluationPeriods'],
        MetricName=awsvars['cpuMetric'],
        Namespace=awsvars['nameSpace'],
        Period=awsvars['period'],
        Statistic=awsvars['cpuStatistic'],
        Threshold=awsvars['cpuThreshold'],
        ActionsEnabled=True,
        AlarmActions=[
            cpu_scale_out_policy['PolicyARN']
        ],
        OKActions=[
            cpu_scale_in_policy['PolicyARN']
        ],
        Dimensions=[
            {
                'Name': 'AutoScalingGroupName',
                'Value': awsvars['autoScalingGroupName']
            },
        ],
        AlarmDescription=awsvars['cpuHighDescription'],
        Unit=awsvars['cpuUnit']
    )

    print("Created High CPU CloudWatch Alarm with parameters: ", high_cpu_alarm)
