import boto3
import json
from datetime import datetime

# Function to convert datetime to a serializable format
def datetime_to_string(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return o

# Function to get detailed information about a user
def get_user_details(iam_client, user_name):
    user_details = iam_client.get_user(UserName=user_name)['User']
    user_details['UserPolicies'] = iam_client.list_user_policies(UserName=user_name)['PolicyNames']
    user_details['AttachedUserPolicies'] = iam_client.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
    user_details['AccessKeys'] = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
    user_details['MFADevices'] = iam_client.list_mfa_devices(UserName=user_name)['MFADevices']
    return user_details

# Function to get information about all IAM groups
def get_iam_groups(iam_client):
    groups = iam_client.list_groups()['Groups']
    for group in groups:
        group['GroupPolicies'] = iam_client.list_group_policies(GroupName=group['GroupName'])['PolicyNames']
        group['AttachedGroupPolicies'] = iam_client.list_attached_group_policies(GroupName=group['GroupName'])['AttachedPolicies']
        group_users = iam_client.get_group(GroupName=group['GroupName'])['Users']
        group['Users'] = [get_user_details(iam_client, user['UserName']) for user in group_users]
    return groups

# Function to get information about all IAM roles
def get_iam_roles(iam_client):
    roles = iam_client.list_roles()['Roles']
    for role in roles:
        role['RolePolicies'] = iam_client.list_role_policies(RoleName=role['RoleName'])['PolicyNames']
        role['AttachedRolePolicies'] = iam_client.list_attached_role_policies(RoleName=role['RoleName'])['AttachedPolicies']
    return roles
def read_config(file_name):
    config = {}
    with open(file_name, 'r') as file:
        for line in file:
            key, value = line.strip().split(': ')
            config[key] = value
    return config

def main():
    iam_client = boto3.client('iam')
    s3_client = boto3.client('s3')

    iam_data = {
        'Groups': get_iam_groups(iam_client),
        'Roles': get_iam_roles(iam_client)
    }

    # Read config file
    config = read_config('config.txt')
    bucket_name = config['bucket']
    folder_path = config['folderpath']

    # Generate JSON content
    iam_json = json.dumps(iam_data, indent=4, default=datetime_to_string)

    # Define object key
    object_key = folder_path + 'aws_iam_data.json'

    # Upload JSON content to S3
    s3_client.put_object(Body=iam_json, Bucket=bucket_name, Key=object_key)

if __name__ == "__main__":
    main()

