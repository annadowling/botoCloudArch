# botoCloudArch
The purpose of this project is to provide an automated method of set up and tear down for a Highly Available, Fault Tolerant, scalable architecture on AWS.
The following items are created and deleted via this project:
1. VPC
2. Public and Private Subnets
3. Security groups at a 3 tier level (Load Balancer Tier, Application Tier and RDS Tier)
4. Route Tables
5. Internet Gateway
6. Application Load Balancer
7. Target Groups
8. AutoScaling Group
9. AutoScaling Launch Configuration
10. RDS Instance
11. EC2 instance in a public Subnet
12. EC2 instances for application launch via AutoScaling Launch Configuration in private subnets and distributed availability zones.
13. AutoScaling Policies
14. CloudWatch Alarms based on metrics for cpu and instance status checks
15. SNS topics associated to above alarms.

## Requirements
The Following packages / tasks need to installed prior to using this project:

1. Install python: sudo yum install python 
2. Install ansible: sudo yum install ansible
3. Install pip:  sudo yum install python-pip
4. sudo python -m pip install boto3

# Credentials
API Keys for use with AWS boto api interaction are housed in ansible encrypted file com/boto/botoScripts/vault.yml 

# How to Run
To run app issue the following command from com/boto/botoScripts: python awsMenu.py

# Example of menu options:
1 Create Scalable AWS Architecture.
2 Delete Scalable AWS Architecture.
3 Exit

1. This Script creates a cli interface to select menu options for creating aws infrastructure.
2. It allows users to create Fully Scalable Architecture.
3. It also allows users to delete / tear down previously created Fully Scalable Architecture.
4. Loads all Architecture variables from  com/boto/botoScripts/awsVariables.yml
5. Loads AWS API keys for use with boto3 from password protected encrypted ansible vault file com/boto/botoScripts/vault.yml


