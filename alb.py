import boto3

def get_elb_clients(aws_profile):
    session = boto3.session.Session(profile_name=aws_profile)

    elb_clients = {
        'us-east-1': session.client("elb", region_name="us-east-1"),
        'eu-west-1': session.client("elb", region_name="eu-west-1")
    }

    return elb_clients

elb_clients = get_elb_clients("devops")

client = boto3.client('autoscaling')

res = client.describe_load_balancers(AutoScalingGroupName="wild-TR-API-CA-ASG-20190304150441283600000003")
#res = client.describe_load_balancers(AutoScalingGroupName="WILD-GATEWAY-CA-ASG-2019030122392700830000002c")

res1 = client.describe_load_balancer_target_groups(AutoScalingGroupName="WILD-GATEWAY-CA-ASG-2019030122392700830000002c")

if res['LoadBalancers']:
	lbs = [lb['LoadBalancerName'] for lb in res['LoadBalancers']]
else:
	lbs = [lb['LoadBalancerTargetGroupARN'] for lb in res1['LoadBalancerTargetGroups']]

#print(res)
#lbs = [lb['LoadBalancerName'] for lb in res['LoadBalancers']]
print(lbs)
#print("")
for elb in lbs:
                attached_instance_states = {instance["InstanceId"]: instance["State"] for instance in elb_clients[asgs_dict[asg]['region']].describe_instance_health(LoadBalancerName=elb)["InstanceStates"]}

print(attached_instance_states)
#print(res1)
#lbs1 = [lb['LoadBalancerTargetGroupARN'] for lb in res1['LoadBalancerTargetGroups']]
#print(lbs1)

