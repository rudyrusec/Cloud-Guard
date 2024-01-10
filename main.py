import boto3
import json
from datetime import datetime
def get_all_regions():
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions
def is_guardduty_enabled(gd_client):
    try:
        detectors = gd_client.list_detectors()
        if detectors['DetectorIds']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking GuardDuty: {e}")
        return False

def check_flow_logs(ec2_client, vpc_id):
    flow_logs = ec2_client.describe_flow_logs(Filters=[{'Name': 'resource-id', 'Values': [vpc_id]}])
    return len(flow_logs['FlowLogs']) > 0

def is_cloudtrail_enabled(ct_client):
    trails = ct_client.describe_trails()
    for trail in trails['trailList']:
        status = ct_client.get_trail_status(Name=trail['TrailARN'])
        if status['IsLogging']:
            return True
    return False

def get_vpcs(ec2_client):
    return ec2_client.describe_vpcs()['Vpcs']

def get_vpc_peerings(ec2_client, vpc_id):
    peerings = ec2_client.describe_vpc_peering_connections(
        Filters=[{'Name': 'requester-vpc-info.vpc-id', 'Values': [vpc_id]}])
    return peerings['VpcPeeringConnections']

def get_subnets(ec2_client, vpc_id):
    return ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']

def get_instances(ec2_client, subnet_id):
    return ec2_client.describe_instances(Filters=[{'Name': 'subnet-id', 'Values': [subnet_id]}])['Reservations']

def get_security_group_details(ec2_client, group_ids):
    security_groups = ec2_client.describe_security_groups(GroupIds=group_ids)['SecurityGroups']
    return security_groups

def get_instance_details(ec2_client, instance):
    instance_details = {
        'InstanceId': instance['InstanceId'],
        'InstanceType': instance['InstanceType'],
        'SecurityGroups': get_security_group_details(ec2_client, [sg['GroupId'] for sg in instance['SecurityGroups']])
    }
    return instance_details
def read_config(file_name):
    config = {}
    with open(file_name, 'r') as file:
        for line in file:
            key, value = line.strip().split(': ')
            config[key] = value
    return config

def datetime_to_string(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return o

def main():
    # Initialize the S3 client
    s3_client = boto3.client('s3')

    # Structure to hold all the infrastructure data
    infrastructure = {}

    # Iterate over all regions
    for region in get_all_regions():
        ec2_client = boto3.client('ec2', region_name=region)
        gd_client = boto3.client('guardduty', region_name=region)
        ct_client = boto3.client('cloudtrail', region_name=region)

        # Initialize region data with GuardDuty and CloudTrail status
        infrastructure[region] = {
            "VPCs": [],
            "GuardDutyEnabled": is_guardduty_enabled(gd_client),
            "CloudTrailEnabled": is_cloudtrail_enabled(ct_client)
        }

        # Iterate over all VPCs in the region
        for vpc in get_vpcs(ec2_client):
            vpc_info = {
                "VpcId": vpc['VpcId'],
                "VpcPeeringConnections": get_vpc_peerings(ec2_client, vpc['VpcId']),
                "Subnets": [],
                "FlowLogsEnabled": check_flow_logs(ec2_client, vpc['VpcId'])
            }

            # Iterate over all subnets in the VPC
            for subnet in get_subnets(ec2_client, vpc['VpcId']):
                subnet_info = {
                    "SubnetId": subnet['SubnetId'],
                    "Instances": []
                }

                # Iterate over all instances in the subnet
                for reservation in get_instances(ec2_client, subnet['SubnetId']):
                    for instance in reservation['Instances']:
                        instance_details = get_instance_details(ec2_client, instance)
                        subnet_info["Instances"].append(instance_details)

                vpc_info["Subnets"].append(subnet_info)

            infrastructure[region]["VPCs"].append(vpc_info)

    # Convert the collected data to JSON
    infrastructure_json = json.dumps(infrastructure, indent=4, default=datetime_to_string)

    # Read the bucket name and folder path from the configuration file
    config = read_config('config.txt')  # Ensure you have the read_config function defined as mentioned earlier
    bucket_name = config['bucket']
    folder_path = config['folderpath']
    object_key = folder_path + 'aws_infrastructure.json'

    # Upload the JSON data to the specified S3 bucket
    s3_client.put_object(Body=infrastructure_json, Bucket=bucket_name, Key=object_key)


if __name__ == "__main__":
    main()
