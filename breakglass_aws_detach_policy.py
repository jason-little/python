# Author Jason Little
# Quick and simple script to detach the AdministratorAccess policy from all users

import boto3

client = boto3.client('iam')

users = client.list_entities_for_policy(PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess")

for i in users["PolicyUsers"]:
	client.detach_user_policy(PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess", UserName=i["UserName"])
