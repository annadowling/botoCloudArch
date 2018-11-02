import boto3
from ansible_vault import Vault


#
# (c) 18/10/2018 A.Dowling
#
# create_sns_topics.py version 1
# boto3
# python version 2.7.14
#
# Creates SNS Email Topics and Subscriptions associated with Scaling events specified:
#
# Creates SNSN topics for specified scaling policies
# Sets topic attributes including name and topic arn
# Subscribes to email notifications for topics for a specified email address
# Assigns the SNS topic notifications to the ASG
# Tags per resource created

def run_sns_topics_script(awsvars, access_key_id, secret_access_key):
    print("Creating SNS Topics")

    sns_client = boto3.client(
        'sns',
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
    create_topics(awsvars, sns_client, asg_client)


def create_topics(awsvars, sns_client, asg_client):
    scale_up_topic = sns_client.create_topic(
        Name=awsvars['scaleUpTopicName'],
    )
    print("Scale Up Topic Created is: ", scale_up_topic['TopicArn'])

    scale_down_topic = sns_client.create_topic(
        Name=awsvars['scaleDownTopicName'],
    )
    print("Scale Down Topic Created is: ", scale_down_topic)
    set_topic_attributes(awsvars, sns_client, asg_client, scale_up_topic, scale_down_topic)


def set_topic_attributes(awsvars, sns_client, asg_client, scale_up_topic, scale_down_topic):
    scale_up_response = sns_client.set_topic_attributes(
        TopicArn=scale_up_topic['TopicArn'],
        AttributeName=awsvars['attributeName'],
        AttributeValue=awsvars['scaleUpNotificationName']
    )
    print("Scale Up notification created is: ", scale_up_response)

    scale_down_response = sns_client.set_topic_attributes(
        TopicArn=scale_down_topic['TopicArn'],
        AttributeName=awsvars['attributeName'],
        AttributeValue=awsvars['scaleDownNotificationName']
    )
    print("Scale Down notification created is: ", scale_down_response)
    subscribe_to_topics(awsvars, sns_client, asg_client, scale_up_topic, scale_down_topic)


def subscribe_to_topics(awsvars, sns_client, asg_client, scale_up_topic, scale_down_topic):
    sns_subscribe_up = sns_client.subscribe(
        TopicArn=scale_up_topic['TopicArn'],
        Protocol=awsvars['topicProtocol'],
        Endpoint=awsvars['emailAddress'],
        ReturnSubscriptionArn=True
    )
    print("Subscribing to Scale Up Events: ", sns_subscribe_up)

    sns_subscribe_down = sns_client.subscribe(
        TopicArn=scale_down_topic['TopicArn'],
        Protocol=awsvars['topicProtocol'],
        Endpoint=awsvars['emailAddress'],
        ReturnSubscriptionArn=True
    )
    print("Subscribing to Scale Down Events: ", sns_subscribe_down)
    set_notifications(awsvars, asg_client, scale_up_topic, scale_down_topic)


def set_notifications(awsvars, asg_client, scale_up_topic, scale_down_topic):
    asg_notification_up = asg_client.put_notification_configuration(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        TopicARN=scale_up_topic['TopicArn'],
        NotificationTypes=[
            awsvars['instanceLaunchNotification'],
        ]
    )
    print("Setting notification type for Scale Up to : ", asg_notification_up)

    asg_notification_down = asg_client.put_notification_configuration(
        AutoScalingGroupName=awsvars['autoScalingGroupName'],
        TopicARN=scale_down_topic['TopicArn'],
        NotificationTypes=[
            awsvars['instanceTerminateNotification'],
        ]
    )
    print("Setting notification type for Scale Down to : ", asg_notification_down)
    print("Completed SNS Topic Setup and Subscription")
