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
        return bool(detectors['DetectorIds'])
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
    vpcs = ec2_client.describe_vpcs()['Vpcs']
    return [
        {
            'VpcId': vpc['VpcId'],
            'VpcName': vpc.get('Tags', [{'Value': 'N/A'}])[0]['Value'],
            'CidrBlock': vpc['CidrBlock']
        } 
        for vpc in vpcs
    ]

def get_subnets(ec2_client, vpc_id):
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
    return [
        {
            'SubnetId': subnet['SubnetId'],
            'SubnetName': subnet.get('Tags', [{'Value': 'N/A'}])[0]['Value'],
            'CidrBlock': subnet['CidrBlock']
        } 
        for subnet in subnets
    ]

def get_instances(ec2_client, subnet_id):
    reservations = ec2_client.describe_instances(Filters=[{'Name': 'subnet-id', 'Values': [subnet_id]}])['Reservations']
    instances = []
    for reservation in reservations:
        for instance in reservation['Instances']:
            instances.append(instance)
    return instances

def get_security_group_details(ec2_client, group_ids):
    security_groups = ec2_client.describe_security_groups(GroupIds=group_ids)['SecurityGroups']
    return [
        {
            'GroupId': sg['GroupId'],
            'GroupName': sg['GroupName'],
            'IpPermissions': [
                {
                    'IpProtocol': perm.get('IpProtocol', 'N/A'),
                    'FromPort': perm.get('FromPort', 'N/A'),
                    'ToPort': perm.get('ToPort', 'N/A'),
                    'IpRanges': perm.get('IpRanges', [])
                } 
                for perm in sg.get('IpPermissions', [])
            ]
        } 
        for sg in security_groups
    ]

def get_instance_details(instance):
    public_ip = instance.get('PublicIpAddress', 'N/A')
    private_ip = instance.get('PrivateIpAddress', 'N/A')
    return {
        'InstanceId': instance['InstanceId'],
        'InstanceType': instance['InstanceType'],
        'PublicIP': public_ip,
        'PrivateIP': private_ip,
        'SecurityGroups': get_security_group_details(boto3.client('ec2'), [sg['GroupId'] for sg in instance['SecurityGroups']])
    }

def datetime_to_string(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return o

def main():
    infrastructure = {}
    for region in get_all_regions():
        ec2_client = boto3.client('ec2', region_name=region)
        gd_client = boto3.client('guardduty', region_name=region)
        ct_client = boto3.client('        cloudtrail', region_name=region)

        infrastructure[region] = {
            "VPCs": [],
            "GuardDutyEnabled": is_guardduty_enabled(gd_client),
            "CloudTrailEnabled": is_cloudtrail_enabled(ct_client)
        }

        for vpc in get_vpcs(ec2_client):
            vpc_info = {
                "VpcId": vpc['VpcId'],
                "VpcName": vpc['VpcName'],
                "CidrBlock": vpc['CidrBlock'],
                "Subnets": [],
                "FlowLogsEnabled": check_flow_logs(ec2_client, vpc['VpcId'])
            }

            for subnet in get_subnets(ec2_client, vpc['VpcId']):
                subnet_info = {
                    "SubnetId": subnet['SubnetId'],
                    "SubnetName": subnet['SubnetName'],
                    "CidrBlock": subnet['CidrBlock'],
                    "Instances": []
                }

                for instance in get_instances(ec2_client, subnet['SubnetId']):
                    instance_details = get_instance_details(instance)
                    subnet_info["Instances"].append(instance_details)

                if subnet_info["Instances"]:
                    vpc_info["Subnets"].append(subnet_info)

            if vpc_info["Subnets"]:
                infrastructure[region]["VPCs"].append(vpc_info)

    infrastructure_json = json.dumps(infrastructure, indent=4, default=datetime_to_string)

    # Here you can add code to save the JSON to a file or an S3 bucket
    # For example, to save it to a file:
    with open('aws_infrastructure.json', 'w') as file:
        file.write(infrastructure_json)

if __name__ == "__main__":
    main()

