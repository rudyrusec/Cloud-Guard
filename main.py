import boto3
import json
def get_all_regions():
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

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

def main():
    infrastructure = {}

    for region in get_all_regions():
        ec2_client = boto3.client('ec2', region_name=region)
        infrastructure[region] = {"VPCs": []}

        for vpc in get_vpcs(ec2_client):
            vpc_info = {
                "VpcId": vpc['VpcId'],
                "VpcPeeringConnections": get_vpc_peerings(ec2_client, vpc['VpcId']),
                "Subnets": []
            }

            for subnet in get_subnets(ec2_client, vpc['VpcId']):
                subnet_info = {
                    "SubnetId": subnet['SubnetId'],
                    "Instances": []
                }

                for reservation in get_instances(ec2_client, subnet['SubnetId']):
                    for instance in reservation['Instances']:
                        instance_details = get_instance_details(ec2_client, instance)
                        subnet_info["Instances"].append(instance_details)

                vpc_info["Subnets"].append(subnet_info)

            infrastructure[region]["VPCs"].append(vpc_info)

    with open('aws_infrastructure.json', 'w') as file:
        json.dump(infrastructure, file, indent=4)


if __name__ == "__main__":
    main()
