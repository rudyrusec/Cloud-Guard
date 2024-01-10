import boto3

def check_security_groups():
    # Create a boto3 EC2 client
    ec2 = boto3.client('ec2')

    # Retrieve all security groups
    response = ec2.describe_security_groups()

    # Check for rules allowing 0.0.0.0/0
    for group in response['SecurityGroups']:
        for permission in group['IpPermissions']:
            for ip_range in permission['IpRanges']:
                if ip_range['CidrIp'] == '0.0.0.0/0':
                    print(f"Security Group '{group['GroupName']}' (ID: {group['GroupId']}) has an open rule: {permission}")

if __name__ == "__main__":
    check_security_groups()
