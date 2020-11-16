import boto3

session = boto3.session.Session(profile_name="devops")

elb_clients = {
    'us-east-1': session.client("elb", region_name="us-east-1"),
    'eu-west-1': session.client("elb", region_name="eu-west-1")
}

print(elb_clients)  
