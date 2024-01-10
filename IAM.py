def get_user_details(iam_client, user_name):
    user_details = iam_client.get_user(UserName=user_name)['User']
    user_details['UserPolicies'] = iam_client.list_user_policies(UserName=user_name)['PolicyNames']
    user_details['AttachedUserPolicies'] = iam_client.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
    user_details['AccessKeys'] = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
    user_details['MFADevices'] = iam_client.list_mfa_devices(UserName=user_name)['MFADevices']
    return user_details

def get_iam_groups(iam_client):
    groups = iam_client.list_groups()['Groups']
    for group in groups:
        group['GroupPolicies'] = iam_client.list_group_policies(GroupName=group['GroupName'])['PolicyNames']
        group['AttachedGroupPolicies'] = iam_client.list_attached_group_policies(GroupName=group['GroupName'])['AttachedPolicies']
        group_users = iam_client.get_group(GroupName=group['GroupName'])['Users']
        group['Users'] = [get_user_details(iam_client, user['UserName']) for user in group_users]
    return groups

def get_iam_roles(iam_client):
    roles = iam_client.list_roles()['Roles']
    for role in roles:
        role['RolePolicies'] = iam_client.list_role_policies(RoleName=role['RoleName'])['PolicyNames']
        role['AttachedRolePolicies'] = iam_client.list_attached_role_policies(RoleName=role['RoleName'])['AttachedPolicies']
    return roles

def main():
    iam_client = boto3.client('iam')
    iam_data = {
        'Groups': get_iam_groups(iam_client),
        'Roles': get_iam_roles(iam_client)
    }

    with open('aws_iam_data.json', 'w') as file:
        json.dump(iam_data, file, indent=4)

if __name__ == "__main__":
    main()
