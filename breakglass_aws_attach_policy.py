# Author Jason Little
# Quick and simple script to attach the AdministratorAccess policy to the users listed in the AdministratorAccess file

import boto3

client = boto3.client('iam')

with open('AdministratorAccess') as f:
	content = f.readlines()

content = [x.strip() for x in content]

for i in content:
	client.attach_user_policy(PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess", UserName=i)
