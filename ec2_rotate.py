#!/usr/bin/env python

import boto3
import os
import pprint
from datetime import datetime
import time
import signal
from termcolor import colored
import argparse
import sys

IS_DRY_RUN = True
IS_PROD = False

SLEEP_INTERVAL_SECONDS = 90

USAGE = """
        Simple tool to perform a rolling update on the ASGs you select. 

        The rolling update doubles the DesiredCapacity and MaxCapacity of the ASG, waits for all instances
        to come into service in the ELB, then sets the DesiredCapacity and MaxCapacity back to their original values.

        Interactive Usage
        -----------------
        After the ASGs are loaded, just type to search for the ASGs you want, then
        follow the on-screen instruction to perform a rolling update.

        {tip} Put a comma between search terms to perform a search with OR separators.
        Example, searching for "test, int" will return any ASGs that have either "test" OR "int" in them.

        Command Line Usage
        ------------------
        To use the non-interactive version of the script, run the script as follows:
            ./ec2_rotate --dry-run --asg ASG-NAME-1 --asg ASG-NAME-2 --profile devops --wait 10 --filter traderev:application==gateway,traderev:region==us --filter traderev:application==ins,traderev:region==us

        All the above arguments are optional.

        --asg is used for you to provide your own ASGs to perform the rolling update on
        --profile is used for you to specify an AWS credentials profile to use. This will be a profile located in ~/.aws/credentials
        --wait is the time to wait in minutes between the scale up and scale down activities
        --filter should be followed by a comma-separated list of tag key-value pairs you want to filter ASGs on
                 Providing more than one --filter will combine the results of each individual --filter

            Sample arguments and their output:

            --filter traderev:application==gateway,traderev:region==us
                Finds all Gateway US ASGs
            --filter traderev:application==gateway
                Finds all Gateways ASGs
            --filter traderev:application==tr-api
                Finds all tr-api ASGs
            --filter traderev:application==gateway,traderev:region==us --filter traderev:application==tr-api
                Finds all Gateway US ASGs and all tr-api ASGs
            --filter traderev:region==us
                Finds all US ASGs

            Generic example:
            --filter tagKeyOne==tagValueOne
                Finds all ASGs which have the tag key "tagKeyOne" that is set to "tagValueOne"
        """
DRY_RUN_NOTICE = colored("DRY_RUN:\n", attrs=["underline"])
SUSPENDED_SCALING_PROCESSES = [
    'ScheduledActions',
    'AlarmNotification',
    'AZRebalance'
]


def run_rolling_update(asg_update_list, asgs_dict, asg_clients, elb_clients, initial_sleep_time, is_alb, scaler):

    completed_asgs = set()

    """
    ******************
    **** SCALE UP ****
    ******************
    """
    if len(asg_update_list) == 0:
        print "No ASGs provided!"
        return 0
    else:
        print "#"*75
        print "Running rolling update on the following ASGs:"
        for asg in asg_update_list:
            print "    - {}".format(asg)
        print ""

    for asg in asg_update_list:
        if asg not in asgs_dict:
            print "{} does not exist! Skipping...\n".format(asg)
            continue

        # Scale up
        region = asgs_dict[asg]['region']

        old_max_size = asgs_dict[asg]['MaxSize']
        if IS_PROD:
            asgs_dict[asg]['NewMaxSize'] = ((old_max_size * 2) + 4) if old_max_size else 0
        else:
            asgs_dict[asg]['NewMaxSize'] = (old_max_size * 2) if old_max_size else 0
        new_max_size = asgs_dict[asg]['NewMaxSize']

        old_desired_capacity = asgs_dict[asg]['DesiredCapacity']
        if IS_PROD:
            asgs_dict[asg]['NewDesiredCapacity'] = ((old_desired_capacity * 2) + 4) if old_desired_capacity else 0
        else:
            asgs_dict[asg]['NewDesiredCapacity'] = (old_desired_capacity * 2) if old_desired_capacity else 0
        new_desired_capacity = asgs_dict[asg]['NewDesiredCapacity']

        if IS_DRY_RUN:
            print DRY_RUN_NOTICE

        print colored("Performing scale UP for {} located in {}".format(asg, region), "blue", "on_white", attrs=["bold"])
        print "     Scaling up DesiredCapacity for {} from {} to {}".format(asg, old_desired_capacity, new_desired_capacity)
        print "     Scaling up MaxSize for {} from {} to {}\n".format(asg, old_max_size, new_max_size)

        if not IS_DRY_RUN:
            asg_clients[region].suspend_processes(
                AutoScalingGroupName=asg,
                ScalingProcesses=SUSPENDED_SCALING_PROCESSES
            )
            if  new_desired_capacity - old_desired_capacity >= scaler:
                # Scale up nicely
                print("Scaling up nicely in increments of %d" % scaler)
                while new_desired_capacity > old_desired_capacity + scaler:
                    old_desired_capacity += scaler
                    asg_clients[region].update_auto_scaling_group(
                        AutoScalingGroupName=asg,
                        MaxSize=new_max_size,
                        DesiredCapacity=old_desired_capacity,
                    )
                    time.sleep(30)

            asg_clients[region].update_auto_scaling_group(
                AutoScalingGroupName=asg,
                MaxSize=new_max_size,
                DesiredCapacity=new_desired_capacity,
            )


    # *************
    # Initial Sleep
    # *************
    print "...Sleep for {} minutes: {}...\n".format(initial_sleep_time, str(datetime.now()))
    seconds_to_sleep = int(initial_sleep_time) * 60
    if not IS_DRY_RUN:
        time.sleep(seconds_to_sleep)

    """
    ******************
    *** SCALE DOWN ***
    ******************
    """
    while set(asg_update_list) != completed_asgs:
        for asg in asg_update_list:
            if asg in completed_asgs:
                continue
            print colored("* Checking ASG: {}".format(asg), attrs=["underline"])
            if asg not in asgs_dict:
                print "{} does not exist! Skipping...\n".format(asg)
                completed_asgs.add(asg)
                continue

            attached_elbs = get_attached_lbs(asg, asg_clients[asgs_dict[asg]['region']])
            print "ELBs attached to {}".format(asg)
            for elb in attached_elbs:
                print "    - {}".format(elb)
            print ""

            all_instances_healthy = True
            for elb in attached_elbs:
                if is_alb:
                    attached_instance_states = {target["Target"]["Id"]: target["TargetHealth"]["State"] for target in elb_clients[asgs_dict[asg]['region']].describe_target_health(TargetGroupArn=elb)["TargetHealthDescriptions"]}
                else:
                    attached_instance_states = {instance["InstanceId"]: instance["State"] for instance in elb_clients[asgs_dict[asg]['region']].describe_instance_health(LoadBalancerName=elb)["InstanceStates"]}

                if len(attached_instance_states) < asgs_dict[asg]['NewDesiredCapacity']:
                    print "{} There are {} instances attached to '{}', but the ASG's DesiredCapacity is {}\n"\
                        .format(colored("NOTE:", "yellow", "on_white", attrs=["bold"]), len(attached_instance_states), elb, asgs_dict[asg]['NewDesiredCapacity'])
                    print colored("Set the DesiredCapacity of {} to {}".format(asg, asgs_dict[asg]['NewDesiredCapacity']), "blue", "on_white", attrs=["bold"])
                    print ""

                    region = asgs_dict[asg]['region']
                    if not IS_DRY_RUN:
                        asg_clients[region].update_auto_scaling_group(
                            AutoScalingGroupName=asg,
                            MaxSize=asgs_dict[asg]['NewMaxSize'],
                            DesiredCapacity=asgs_dict[asg]['NewDesiredCapacity'],
                        )
                    all_instances_healthy = False
                    break

                if is_alb:
                    attached_instances_healthy = map(lambda x: x == 'healthy', attached_instance_states.values())

                else:
                    attached_instances_healthy = map(lambda x: x == 'InService', attached_instance_states.values())

                print "Instance states for {}:".format(elb)
                pprint.pprint(attached_instance_states)
                print ""

                all_instances_healthy = all(attached_instances_healthy) & all_instances_healthy
                if not all_instances_healthy:
                    print "Some instances in {} are not InService....\n".format(elb)
                    break

            if all_instances_healthy or IS_DRY_RUN or not IS_PROD:
                # Scale down
                region = asgs_dict[asg]['region']

                old_max_size = asgs_dict[asg]['MaxSize']
                new_max_size = asgs_dict[asg]['NewMaxSize']

                old_desired_capacity = asgs_dict[asg]['DesiredCapacity']
                new_desired_capacity = asgs_dict[asg]['NewDesiredCapacity']

                if IS_DRY_RUN:
                    print DRY_RUN_NOTICE
                print colored("Performing scale DOWN for {} located in {}".format(asg, region), "red", "on_white", attrs=["bold"])
                print "     Scaling down DesiredCapacity for {} from {} to {}".format(asg, new_desired_capacity, old_desired_capacity)
                print "     Scaling down MaxSize for {} from {} to {}\n".format(asg, new_max_size, old_max_size)

                if not IS_DRY_RUN:
                    if new_desired_capacity - old_desired_capacity >= scaler:
                        print("Scaling down nicely in increments of %d" % scaler)
                        while new_desired_capacity > old_desired_capacity + scaler:
                            new_desired_capacity -= scaler
                            asg_clients[region].update_auto_scaling_group(
                                AutoScalingGroupName=asg,
                                MaxSize=new_max_size,
                                DesiredCapacity=new_desired_capacity,
                            )
                            time.sleep(30)

                    asg_clients[region].update_auto_scaling_group(
                        AutoScalingGroupName=asg,
                        MaxSize=old_max_size,
                        DesiredCapacity=old_desired_capacity,
                    )
                    if IS_PROD:
                        # in prod, sleep for a little minutes to make sure the instances have scaled back down again
                        # otherwise, scaling processes will mess up the desired capacity.
                        scale_down_sleep = 30
                        print "...Sleep for {} seconds while scaling down...{}\n".format(scale_down_sleep, str(datetime.now()))
                        time.sleep(scale_down_sleep)
                    asg_clients[region].resume_processes(
                        AutoScalingGroupName=asg,
                        ScalingProcesses=SUSPENDED_SCALING_PROCESSES
                    )

                completed_asgs.add(asg)

        if set(asg_update_list) != completed_asgs:
            print "[Rolling update is still in progress for the following ASGs:]"
            for asg in list(set(asg_update_list)-completed_asgs):
                print "    - {}".format(asg)
            print ""
            print "...Sleep for {} seconds before retrying: {}...\n".format(SLEEP_INTERVAL_SECONDS, str(datetime.now()))
            print "*"*75

            time.sleep(SLEEP_INTERVAL_SECONDS)  # sleep for a minute, then try again

    print colored("All rolling updates completed successfully!", "green", "on_white", attrs=["bold"])

def run_scale_down_only(asg_update_list, asgs_dict, asg_clients, elb_clients, is_alb):

    downscaled_asgs = set()

    if len(asg_update_list) == 0:
        print "No ASGs provided!"
        return 0
    else:
        print "#"*75
        print "Running scale down on the following ASGs:"
        for asg in asg_update_list:
            print "    - {}".format(asg)
        print ""

    asgs_dict[asg]['NewMinSize'] = 0
    asgs_dict[asg]['NewDesiredCapacity'] = 0
    asgs_dict[asg]['NewMaxSize'] = 0

    scale_asgs(asg_clients, asgs_dict, asg_update_list, asgs_dict[asg]['NewMinSize'], asgs_dict[asg]['NewDesiredCapacity'], asgs_dict[asg]['NewMaxSize'])

    wait_for_asg_scale_completion(asg_update_list, downscaled_asgs, asgs_dict[asg]['NewDesiredCapacity'], elb_clients, is_alb)

    print colored("All scale downs have completed successfully!", "green", "on_white", attrs=["bold"])

def run_scale_up_only(asg_update_list, asgs_dict, asg_clients, elb_clients, is_alb, desired_capacity):

    scaledup_asgs = set()

    if len(asg_update_list) == 0:
        print "No ASGs provided!"
        return 0
    else:
        print "#"*75
        print "Running scale up on the following ASGs:"
        for asg in asg_update_list:
            print "    - {}".format(asg)
        print ""

    asgs_dict[asg]['NewMinSize'] = desired_capacity
    asgs_dict[asg]['NewDesiredCapacity'] = desired_capacity
    asgs_dict[asg]['NewMaxSize'] = desired_capacity

    scale_asgs(asg_clients, asgs_dict, asg_update_list, asgs_dict[asg]['NewMinSize'], asgs_dict[asg]['NewDesiredCapacity'], asgs_dict[asg]['NewMaxSize'])

    wait_for_asg_scale_completion(asg_update_list, scaledup_asgs, asgs_dict[asg]['NewDesiredCapacity'], elb_clients, is_alb)

    print colored("All scale ups have completed successfully!", "green", "on_white", attrs=["bold"])

def run_rolling_update_worker_node(asg_update_list, asgs_dict, asg_clients, elb_clients, is_alb):

    downscaled_asgs = set()
    completed_asgs = set()

    if len(asg_update_list) == 0:
        print "No ASGs provided!"
        return 0
    else:
        print "#"*75
        print "Running rolling update on the following ASGs:"
        for asg in asg_update_list:
            print "    - {}".format(asg)
        print ""

    asgs_dict[asg]['NewMinSize'] = 0
    asgs_dict[asg]['NewDesiredCapacity'] = 0
    asgs_dict[asg]['NewMaxSize'] = 0

    scale_asgs(asg_clients, asgs_dict, asg_update_list, asgs_dict[asg]['NewMinSize'], asgs_dict[asg]['NewDesiredCapacity'], asgs_dict[asg]['NewMaxSize'])

    wait_for_asg_scale_completion(asg_update_list, downscaled_asgs, asgs_dict[asg]['NewDesiredCapacity'], elb_clients, is_alb)

    if asgs_dict[asg]['DesiredCapacity'] == 0:
        asgs_dict[asg]['MinSize'] = 1
        asgs_dict[asg]['DesiredCapacity'] = 1
        asgs_dict[asg]['MaxSize'] = 5

    print colored("Scale down completed. Proceeding to Scale up", "green", "on_white", attrs=["bold"])

    scale_asgs(asg_clients, asgs_dict, asg_update_list, asgs_dict[asg]['MinSize'], asgs_dict[asg]['DesiredCapacity'], asgs_dict[asg]['MaxSize'])

    wait_for_asg_scale_completion(asg_update_list, completed_asgs, asgs_dict[asg]['DesiredCapacity'], elb_clients, is_alb)

    print colored("All rolling updates completed successfully!", "green", "on_white", attrs=["bold"])

def print_remaining_asg_and_sleep(asg_update_list, completed_asgs):
    print "[Rolling update is still in progress for the following ASGs:]"
    for asg in list(set(asg_update_list)-completed_asgs):
        print "    - {}".format(asg)
    print ""
    print "...Sleep for {} seconds before retrying: {}...\n".format(SLEEP_INTERVAL_SECONDS, str(datetime.now()))
    print "*"*75
    time.sleep(SLEEP_INTERVAL_SECONDS)

def filter_healthy(target):
    unhealthy = ['initial', 'unhealthy', 'unused', 'draining','unavailable', 'OutOfService']

    if target not in unhealthy:
        return True
    else:
        return False

def scale_asgs(asg_clients, asgs_dict, asg_update_list, min, desired, max):
    for asg in asg_update_list:
        if asg not in asgs_dict:
            print "{} does not exist! Skipping...\n".format(asg)
            continue

        if IS_DRY_RUN:
            print DRY_RUN_NOTICE

        print colored("Performing scale for {} located in {}".format(asg, asgs_dict[asg]['region']), "blue", "on_white", attrs=["bold"])
        print "     Scaling DesiredCapacity for {} to {}".format(asg, desired)
        print "     Scaling MinSize for {} to {}\n".format(asg, min)
        print "     Scaling MaxSize for {} to {}\n".format(asg, max)

        if not IS_DRY_RUN:
            scale(asg_clients, asg, asgs_dict[asg]['region'], min, desired, max)

def scale(asg_clients, asg, region, min, desired, max):
    asg_clients[region].update_auto_scaling_group(
        AutoScalingGroupName=asg,
        MinSize=min,
        MaxSize=max,
        DesiredCapacity=desired
    )
    if IS_PROD:
        scale_down_sleep = 30
        print "...Sleep for {} seconds while scaling {}\n".format(scale_down_sleep, str(datetime.now()))
        time.sleep(scale_down_sleep)
    asg_clients[region].suspend_processes(
        AutoScalingGroupName=asg,
        ScalingProcesses=SUSPENDED_SCALING_PROCESSES
    )

def is_elb_match_asg(asg, asgs_dict, elb, elb_clients, desired_capacity, is_alb):
    attached_target_states = get_attached_targets(asg, asgs_dict, elb, elb_clients, is_alb)
    print "{} There are {} instances attached to '{}' Here they are: {}\n" \
        .format(colored("NOTE:", "yellow", "on_white", attrs=["bold"]), len(attached_target_states), elb, attached_target_states)
    if desired_capacity == 0 :
        if len(attached_target_states.keys()) == 0:
            return True
        else:
            print "{} There are {} instances attached to '{}', but the ASG's DesiredCapacity is {}\n" \
                .format(colored("NOTE:", "yellow", "on_white", attrs=["bold"]), len(attached_target_states), elb, desired_capacity)
            print ""
            return False
    elif desired_capacity != 0:
        if len(filter(filter_healthy, attached_target_states.values())) >= desired_capacity:
            return True
        else:
            print "{} There are {} instances attached to '{}' Here they are: {}\n" \
                .format(colored("NOTE:", "yellow", "on_white", attrs=["bold"]), len(attached_target_states), elb, attached_target_states)
            return False

def get_attached_targets(asg, asgs_dict, elb, elb_clients, is_alb):
    if is_alb:
        return {target["Target"]["Id"]: target["TargetHealth"]["State"] for target in elb_clients[asgs_dict[asg]['region']].describe_target_health(TargetGroupArn=elb)["TargetHealthDescriptions"]}
    else:
        return {instance["InstanceId"]: instance["State"] for instance in elb_clients[asgs_dict[asg]['region']].describe_instance_health(LoadBalancerName=elb)["InstanceStates"]}

def is_asg_fit_for_elb_test(asg, asgs_dict, completed_asgs):
    if asg in completed_asgs:
        return False
    print colored("* Checking ASG: {}".format(asg), attrs=["underline"])
    if asg not in asgs_dict:
        print "{} does not exist! Skipping...\n".format(asg)
        completed_asgs.add(asg)
        return False
    return True

def get_attached_elb_tgs(asg, client, is_alb):
    if is_alb:
        res = client.describe_load_balancer_target_groups(AutoScalingGroupName=asg)
        lbs = [lb['LoadBalancerTargetGroupARN'] for lb in res['LoadBalancerTargetGroups']]
        return lbs
    else:
        res = client.describe_load_balancers(AutoScalingGroupName=asg)
        lbs = [lb['LoadBalancerName'] for lb in res['LoadBalancers']]
        return lbs

def wait_for_asg_scale_completion(asg_update_list, completed_asgs, desired_capacity, elb_clients, is_alb):
    while set(asg_update_list) != completed_asgs:
        print_remaining_asg_and_sleep(asg_update_list, completed_asgs)
        for asg in asg_update_list:
            if not is_asg_fit_for_elb_test(asg, asgs_dict, completed_asgs):
                print "ASG {} is not fit to be tested\n".format(asg)
                continue
            attached_elbs = get_attached_elb_tgs(asg, asg_clients[asgs_dict[asg]['region']], is_alb)
            print "Attached ELBs:\n".format(attached_elbs)
            for elb in attached_elbs:
                print "ELBs attached to {}".format(asg)
                print "    - {}".format(elb)
                if is_elb_match_asg(asg, asgs_dict, elb, elb_clients, desired_capacity, is_alb):
                    completed_asgs.add(asg)

def get_asg_clients(aws_profile):
    session = boto3.session.Session(profile_name=aws_profile)

    asg_clients = {
        'us-east-1': session.client("autoscaling", region_name="us-east-1"),
        'eu-west-1': session.client("autoscaling", region_name="eu-west-1")
    }

    return asg_clients


def get_elb_clients(aws_profile):
    session = boto3.session.Session(profile_name=aws_profile)

    elb_clients = {
        'us-east-1': session.client("elb", region_name="us-east-1"),
        'eu-west-1': session.client("elb", region_name="eu-west-1")
    }

    return elb_clients

def get_elbv2_clients(aws_profile):
    session = boto3.session.Session(profile_name=aws_profile)

    elb_clients = {
        'us-east-1': session.client("elbv2", region_name="us-east-1"),
        'eu-west-1': session.client("elbv2", region_name="eu-west-1")
    }

    return elb_clients


def get_aws_account_id(aws_profile):
    session = boto3.session.Session(profile_name=aws_profile)
    aws_account_id = session.client("sts", region_name="us-east-1").get_caller_identity().get('Account')

    return aws_account_id


def get_asgs(asg_clients):
    """
    Returns a list of all the ASGs which can be found under the regions in the asg_clients
    """
    asgs_dict = {}

    print "Getting list of AutoScalingGroups...\n"
    for region in asg_clients:
        asgs = []
        asgs_initial_res = asg_clients[region].describe_auto_scaling_groups(MaxRecords=100)
        asgs += asgs_initial_res['AutoScalingGroups']
        while asgs_initial_res.get("NextToken", None):
            asgs_initial_res = asg_clients[region].describe_auto_scaling_groups(MaxRecords=100, NextToken=asgs_initial_res['NextToken'])
            asgs += asgs_initial_res['AutoScalingGroups']
        for asg in asgs:
            name = asg['AutoScalingGroupName']
            asg['region'] = region
            if not asgs_dict.get(name):
                asgs_dict[name] = asg
            else:
                print "Duplicate ASG name detected!"

    return asgs_dict

def get_attached_lbs(asg, client):
    res = client.describe_load_balancers(AutoScalingGroupName=asg)
    res1 = client.describe_load_balancer_target_groups(AutoScalingGroupName=asg)

    if IS_ALB:
        lbs = [lb['LoadBalancerTargetGroupARN'] for lb in res1['LoadBalancerTargetGroups']]
    else:
        lbs = [lb['LoadBalancerName'] for lb in res['LoadBalancers']]
    
    return lbs


def create_tag_filters_list(filters):
    """
    Takes in the passed --tag filters list and returns a list of dicts with tag keys and values

    Example:
        When "--filter traderev:application==gateway,traderev:region==us --filter traderev:application==ins,traderev:region==us" is passed through the command line,
        then ["traderev:application==gateway,traderev:region==us",
              "traderev:application==ins,traderev:region==us"] is passed into this function
        which returns [{'TRADEREV:APPLICATION': 'GATEWAY', 'TRADEREV:REGION': 'US'},
                       {'TRADEREV:APPLICATION': 'INS', 'TRADEREV:REGION': 'US'}]
    """
    tag_filters_list = []

    for idx, tagged in enumerate(filters):
        tag_filters_list.append({})
        tagKeys_tagVals = tagged.split(",")
        for key_val in tagKeys_tagVals:
            if "==" not in key_val:
                print "Bad format for tag key-value pair: {}".format(key_val)
                print "Make sure you use '=='!"
                exit(1)
            tagKey = key_val.split("==")[0].upper()
            tagVal = key_val.split("==")[1].upper()
            if tag_filters_list[idx].get(tagKey):
                print "Duplicate tag key detected: {}".format(tagKey)
                exit(1)
            tag_filters_list[idx][tagKey] = tagVal

    return tag_filters_list


def filter_asgs(asgs_dict, tag_filters_list):
    """
    Filters a dictionary of ASGs using the provided tag_filters_list

    Example: If tag_filters_list is [{'TRADEREV:APPLICATION': 'GATEWAY', 'TRADEREV:REGION': 'US'},
                                     {'TRADEREV:APPLICATION': 'INS', 'TRADEREV:REGION': 'US'}]

             the function returns a list of ASGs which have either
             {'TRADEREV:APPLICATION': 'GATEWAY', 'TRADEREV:REGION': 'US'} in their tags,
             or
             {'TRADEREV:APPLICATION': 'INS', 'TRADEREV:REGION': 'US'}.

             The tag_filters_list can contain any number of dictionaries with any numbers of tag-key:tag-val pairs
    """
    filtered_asgs = []

    for asg, asg_info in asgs_dict.iteritems():
        if asg in filtered_asgs:
            continue
        asg_tags = asg_info['Tags']
        asg_tags_dict = {}
        for tag in asg_tags:
            asg_tags_dict[tag['Key'].upper()] = tag['Value'].upper()

        for tag_filters in tag_filters_list:
            matches = True
            for tag_filter_key, tag_filter_val in tag_filters.iteritems():
                matches = matches and asg_tags_dict.get(tag_filter_key) == tag_filter_val
            if matches:
                filtered_asgs.append(asg)
                break

    return filtered_asgs


def print_help():
    note = colored("Note:", "red", "on_white", attrs=["bold"])
    tip = colored("Tip:", "red", "on_white", attrs=["bold"])

    print USAGE.format(tip=tip, note=note)


####################################################
####################### MAIN #######################
####################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', action='store', dest='aws_profile', default=None)
    parser.add_argument('--dry-run', action='store_true', dest='dry_run', default=False)
    parser.add_argument('--wait', action='store', dest='wait_time', default=5, help="Time to wait in minutes between the scale up and scale down")
    parser.add_argument('--asg', action='append', dest='asgs', default=[])
    parser.add_argument('--filter', action='append', dest='filters', default=[])
    parser.add_argument('--worker-node', action='store_true', dest='worker_node', default=False)
    parser.add_argument('--is-alb', action='store_true', dest='is_alb', default=False)
    parser.add_argument('--scale-down', action='store_true', dest='scale_down_only', default=False)
    parser.add_argument('--scale-up', action='store_true', dest='scale_up_only', default=False)
    parser.add_argument('--desired-capacity', action='store', dest='desired_capacity', default=0)
    parser.add_argument('--scaler', type=int, action='store', dest='scaler', default=10)

    args = parser.parse_args()

    MINUTES_TO_SLEEP = args.wait_time
    IS_DRY_RUN = args.dry_run
    IS_WORKER_NODE = args.worker_node
    SCALE_DOWN_ONLY = args.scale_down_only
    SCALE_UP_ONLY = args.scale_up_only
    DESIRED_CAPACITY = int(args.desired_capacity)
    IS_ALB = args.is_alb
    SCALER = args.scaler

    aws_account_id = get_aws_account_id(args.aws_profile)

    IS_PROD = True if (aws_account_id == "374725791127") else False

    asg_clients = get_asg_clients(args.aws_profile)
    elb_clients = get_elb_clients(args.aws_profile)
    elbv2_clients = get_elbv2_clients(args.aws_profile)
    asgs_dict = get_asgs(asg_clients)

    # NON-INTERACTIVE MODE:
    #     This mode is used if you pass any ASGs or tag key-value pairs to filter ASGs on.
    if args.asgs or args.filters:
        tag_filters_list = create_tag_filters_list(args.filters)

        print "Tag Filters:"
        print(tag_filters_list)

        filtered_asgs = filter_asgs(asgs_dict, tag_filters_list)

        asg_update_list = args.asgs + filtered_asgs
        asg_update_list = sorted(asg_update_list)

        if SCALE_DOWN_ONLY:
            if IS_ALB:
                run_scale_down_only(asg_update_list, asgs_dict, asg_clients, elbv2_clients, IS_ALB)
            else:
                run_scale_down_only(asg_update_list, asgs_dict, asg_clients, elb_clients, IS_ALB)
        elif SCALE_UP_ONLY:
            if IS_ALB:
                run_scale_up_only(asg_update_list, asgs_dict, asg_clients, elbv2_clients, IS_ALB, DESIRED_CAPACITY)
            else:
                run_scale_up_only(asg_update_list, asgs_dict, asg_clients, elb_clients, IS_ALB, DESIRED_CAPACITY)
        elif IS_WORKER_NODE:
            if IS_ALB:
                run_rolling_update_worker_node(asg_update_list, asgs_dict, asg_clients, elbv2_clients, IS_ALB)
            else:
                run_rolling_update_worker_node(asg_update_list, asgs_dict, asg_clients, elb_clients, IS_ALB)
        else:
            if IS_ALB:
                run_rolling_update(asg_update_list, asgs_dict, asg_clients, elbv2_clients, MINUTES_TO_SLEEP, IS_ALB, SCALER)
            else:
                run_rolling_update(asg_update_list, asgs_dict, asg_clients, elb_clients, MINUTES_TO_SLEEP, IS_ALB, SCALER)

    # INTERACTIVE MODE
    else:
        pp = pprint.PrettyPrinter(width=10)

        print_help()

        asgs = sorted(asgs_dict.keys(), key=lambda x: x.lower())
        pp.pprint(asgs)

        print "Ready...\n"
        prompt = "Type something to search" if not IS_DRY_RUN else "(DRY_RUN) Type something to search"
        print prompt

        results = {}
        while True:
            user_input = raw_input("> ")
            if user_input == "help":
                print "ls: list all autoscaling groups"
                print "exit: exit the script"
                continue
            elif user_input.startswith("/r"):
                asg_update_list = user_input.strip()[3:]

                if not asg_update_list:
                  print "No LIST_IDs provided!"
                  continue
                else:
                    asg_update_list = asg_update_list.split(" ")

                if len(asg_update_list) > len(results):
                    print "Error: Too many AutoScalingGroups specified"
                else:
                    asg_update_list = [results[int(i)] for i in asg_update_list]
                    if SCALE_DOWN_ONLY:
                        if IS_ALB:
                            run_scale_down_only(asg_update_list, asgs_dict, asg_clients, elbv2_clients, IS_ALB)
                        else:
                            run_scale_down_only(asg_update_list, asgs_dict, asg_clients, elb_clients, IS_ALB)
                    elif SCALE_UP_ONLY:
                        if IS_ALB:
                            run_scale_up_only(asg_update_list, asgs_dict, asg_clients, elbv2_clients, IS_ALB, DESIRED_CAPACITY)
                        else:
                            run_scale_up_only(asg_update_list, asgs_dict, asg_clients, elb_clients, IS_ALB, DESIRED_CAPACITY)
                    elif IS_WORKER_NODE:
                        if IS_ALB:
                            run_rolling_update_worker_node(asg_update_list, asgs_dict, asg_clients, elbv2_clients, IS_ALB)
                        else:
                            run_rolling_update_worker_node(asg_update_list, asgs_dict, asg_clients, elb_clients, IS_ALB)
                    else:
                        run_rolling_update(asg_update_list, asgs_dict, asg_clients, elb_clients, MINUTES_TO_SLEEP, IS_ALB, SCALER)
                continue
            elif user_input == "exit":
                exit(0)
            elif user_input == "ls":
                pp.pprint(asgs)
                continue
            else:
                # Return the search results
                results = {}
                i = 1
                for asg in asgs:
                    user_inputs = [input.strip() for input in user_input.split(",")]
                    if any(input.upper() in asg.upper() for input in user_inputs):
                        results[i] = asg
                        i += 1

                pp.pprint (results)
                print "\nType '/r [LIST_ID] [LIST_ID] [LIST_ID]' to perform a rolling update\n"
