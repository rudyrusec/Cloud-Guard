import json
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

def apply_shape_and_color(G, node, shape, status=None):
    G.nodes[node]['shape'] = shape
    if status is not None:
        G.nodes[node]['color'] = 'green' if status else 'red'
        G.nodes[node]['style'] = 'filled'

def generate_graph(data):
    G = nx.DiGraph()

    for region, region_data in data.items():
        region_node = f"Region: {region}"
        G.add_node(region_node, shape="rectangle")
        apply_shape_and_color(G, region_node, "rectangle")

        gd_status = f"GuardDuty: {'Enabled' if region_data['GuardDutyEnabled'] else 'Disabled'}"
        G.add_node(gd_status, shape="hexagon")
        apply_shape_and_color(G, gd_status, "hexagon", region_data["GuardDutyEnabled"])
        G.add_edge(region_node, gd_status)

        ct_status = f"CloudTrail: {'Enabled' if region_data['CloudTrailEnabled'] else 'Disabled'}"
        G.add_node(ct_status, shape="hexagon")
        apply_shape_and_color(G, ct_status, "hexagon", region_data["CloudTrailEnabled"])
        G.add_edge(region_node, ct_status)

        for vpc in region_data["VPCs"]:
            vpc_id = f"VPC: {vpc['VpcId']}\nName: {vpc['VpcName']}\nCIDR: {vpc['CidrBlock']}"
            G.add_node(vpc_id, shape="ellipse")
            apply_shape_and_color(G, vpc_id, "ellipse")
            G.add_edge(region_node, vpc_id)

            flow_log_status = f"Flow Logs: {'Enabled' if vpc['FlowLogsEnabled'] else 'Disabled'}"
            G.add_node(flow_log_status, shape="hexagon")
            apply_shape_and_color(G, flow_log_status, "hexagon", vpc["FlowLogsEnabled"])
            G.add_edge(vpc_id, flow_log_status)

            for subnet in vpc["Subnets"]:
                subnet_id = f"Subnet: {subnet['SubnetId']}\nName: {subnet['SubnetName']}\nCIDR: {subnet['CidrBlock']}"
                G.add_node(subnet_id, shape="diamond")
                apply_shape_and_color(G, subnet_id, "diamond")
                G.add_edge(vpc_id, subnet_id)

                for instance in subnet["Instances"]:
                    instance_details = f"Instance: {instance['InstanceId']}\nType: {instance['InstanceType']}\nPublic IP: {instance['PublicIP']}\nPrivate IP: {instance['PrivateIP']}"
                    G.add_node(instance_details, shape="house")
                    apply_shape_and_color(G, instance_details, "house")
                    G.add_edge(subnet_id, instance_details)

                    for sg in instance["SecurityGroups"]:
                        sg_details = f"SG: {sg['GroupId']}\n({sg['GroupName']})"
                        G.add_node(sg_details, shape="parallelogram")
                        apply_shape_and_color(G, sg_details, "parallelogram")
                        G.add_edge(instance_details, sg_details)

    return G

def draw_graph(G):
    plt.figure(figsize=(18, 18))
    pos = graphviz_layout(G, prog='dot')
    nx.draw(G, pos, with_labels=True, arrows=True, node_size=2500, font_size=8)
    plt.title("AWS Network Configuration", fontsize=15)
    plt.show()

def main(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    G = generate_graph(data)
    draw_graph(G)

if __name__ == "__main__":
    json_file = 'aws_infrastructure.json'  # Replace with your JSON file path
    main(json_file)
