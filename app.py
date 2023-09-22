#!/usr/bin/env python3

import yaml
from argparse import ArgumentParser
from main.usercreator import KubernetesUserCreator
from main.crbcreator import KubernetesClusterRoleBinding
from main.rbcreator import K8sRoleAndRoleBinding

version = '1.2.2'

def read_config(file_path: str) -> dict:
    with open(file_path, 'r') as yaml_file:
        try:
            app_config = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            print(f"Error reading configuration file: {e}")
            raise
    return app_config

def create_user_and_cluster_role_bindings(app_config: dict, user: str, clusters: str, role: str):
    cluster_list = clusters.split(",")  # "dev" or "dev,stage,prod"

    user_creator = KubernetesUserCreator(app_config, user, cluster_list, role)
    user_creator.create_user()

    crb_creator = KubernetesClusterRoleBinding(app_config, user, cluster_list, role)
    crb_creator.create_clusterrole()
    crb_creator.create_clusterrolebinding_if_not_exists()

def create_namespace_roles_and_bindings(user: str, clusters: str, namespaces: str, role_name: str):
    cluster_list = clusters.split(",")  # "dev" or "dev,stage,prod
    ns_list = namespaces.split(",")  # "ns" or "ns1,ns2,ns3"

    rb_creator = K8sRoleAndRoleBinding(user, cluster_list, ns_list, role_name)
    rb_creator.create_role()
    rb_creator.create_role_binding()

def main():
    parser = ArgumentParser(description=f'Kubernetes RBAC Management Tool v{version}')
    parser.add_argument('user', help='Username')
    parser.add_argument('--cluster', help='Cluster or list of clusters (comma-separated)')
    parser.add_argument('--namespace', default=None, help='Namespace or list of namespaces (comma-separated)')
    parser.add_argument('--role', default=None, help='Roles in cluster (mathes to "cluster_roles" list in app.config.yml)')
    parser.add_argument('--rolens',  default=None, help='Role in Namespace')
    parser.add_argument('--config', default='app.config.yaml', help='Path to the configuration file')

    args = parser.parse_args()
    app_config = read_config(args.config)

    if args.role:
        #example run: app.py j.doe --cluster dev,prod --role developer
        create_user_and_cluster_role_bindings(app_config, args.user, args.cluster, args.role)
    elif args.namespace and args.rolens: 
        #example run: app.py j.doe --cluster dev,prod --namespace test-ns1,test-ns2,test-ns3 --rolens namespace-admin
        create_namespace_roles_and_bindings(args.user, args.cluster, args.namespace, args.rolens)

if __name__ == "__main__":
    main()
