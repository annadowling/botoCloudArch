from ansible_vault import Vault
import yaml
import create_vpc
import create_rds
import create_alb
import create_autoscaling_group
import create_ec2_instance
import create_cloudwatch_monitoring
import create_sns_topics
import teardown_aws_architecture

#
# (c) 23/10/2018 A.Dowling
#
# awsMenu.py version 1
# boto3
# python version 2.7.14
#
# Script creates cli interface to select menu options for creating aws infrastructure.
# Allows users to create Fully Scalable Architecture.
# Allows users to delete / tear down previously created Fully Scalable Architecture.
# Loads all Architecture variables for awsVariables.yml
# Loads AWS API keys for use with boto3 from password protected encrypted ansible vault file vault.yml
#
# command to run example: python awsMenu.py

awsvars = yaml.load(open("awsVariables.yml"))

password = raw_input("Please enter API Key password: ")
print("you entered" + password)
vault = Vault(password)

key_data = vault.load(open('vault.yml').read())
secret_access_key = list(key_data.values())[0]
access_key_id = list(key_data.values())[1]

menu = {}
menu['1'] = "Create Scalable AWS Architecture."
menu['2'] = "Delete Scalable AWS Architecture."
menu['3'] = "Exit"
while True:
    options = menu.keys()
    options.sort()
    for entry in options:
        print entry, menu[entry]

    selection = raw_input("Please Select an Option:")
    if selection == '1':
        create_vpc.run_vpc_script(awsvars, access_key_id, secret_access_key)
        create_rds.run_rds_script(awsvars, access_key_id, secret_access_key)
        create_ec2_instance.run_ec2_script(awsvars, access_key_id, secret_access_key)
        create_alb.run_alb_script(awsvars, access_key_id, secret_access_key)
        create_autoscaling_group.run_asg_script(awsvars, access_key_id, secret_access_key)
        create_cloudwatch_monitoring.run_cloudwatch_script(awsvars, access_key_id, secret_access_key)
        create_sns_topics.run_sns_topics_script(awsvars, access_key_id, secret_access_key)
    elif selection == '2':
        teardown_aws_architecture.run_delete_script(awsvars, access_key_id, secret_access_key)
    elif selection == '3':
        break
    else:
        print "Unknown Option Selected!"
