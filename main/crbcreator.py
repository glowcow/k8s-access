#!/usr/bin/env python3

from kubernetes import client
from kubernetes.client.rest import ApiException
from main.colors import bc
from main.kubeapi import KubeApi
import yaml

class KubernetesClusterRoleBinding:

    def __init__(self, app_config, user, clusters, cluster_role):
        self.app_config = app_config
        self.clusters = clusters
        self.user = user
        self.cluster_role = cluster_role

        self.k8s = KubeApi(self.clusters)
        self.kube_clients = self.k8s.kube_clients_rbac()

        self.subjects =  [
        client.V1Subject(
            api_group="rbac.authorization.k8s.io",
            kind = "User",
            name = self.user
        )
    ]

    def create_clusterrole(self):
        for cluster in self.clusters:
            clusterroles = self.app_config["clusters"][cluster]["cluster_roles"][self.cluster_role]
            for clusterole_ in clusterroles:
                with open(f'templates/{clusterole_}.yaml', 'r') as f:
                    role_data = yaml.safe_load(f)
                metadata = role_data['metadata']
                rules = [client.V1PolicyRule(api_groups=rule['apiGroups'], resources=rule['resources'], verbs=rule['verbs'])
                         for rule in role_data['rules']]
                try:
                    kube_client = self.kube_clients[cluster]
                    clusterrole = client.V1ClusterRole(metadata=client.V1ObjectMeta(**metadata), rules=rules)
                    kube_client.create_cluster_role(body=clusterrole)
                    print(f"{bc.GREEN}  :+:{cluster}:  ClusterRole {bc.ENDC}'{clusterole_}' {bc.GREEN}created{bc.ENDC}")
                except ApiException as e:
                    if e.status == 409:
                        print(f"{bc.YELLOW}  :!:{cluster}:  ClusterRole {bc.ENDC}'{clusterole_}' {bc.YELLOW}already exists{bc.ENDC}")
                    else:
                        raise

    def get_clusterrolebinding(self, name, cluster):
        kube_client = self.kube_clients[cluster]
        try:
            return kube_client.read_cluster_role_binding(name)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return None
            raise

    def create_clusterrolebinding(self, name, cluster_role_name, cluster):
        kube_client = self.kube_clients[cluster]
        body = client.V1ClusterRoleBinding(
            api_version="rbac.authorization.k8s.io/v1",
            kind="ClusterRoleBinding",
            metadata=client.V1ObjectMeta(name=name),
            role_ref=client.V1RoleRef(
                api_group="rbac.authorization.k8s.io",
                kind="ClusterRole",
                name=cluster_role_name
            ),
            subjects=self.subjects
        )

        kube_client.create_cluster_role_binding(body)

    def create_clusterrolebinding_if_not_exists(self):
        for cluster in self.clusters:
            for cluster_role in self.app_config["clusters"][cluster]["cluster_roles"][self.cluster_role]:
                name = f'{cluster_role}:{self.user}'
                existing_clusterrolebinding = self.get_clusterrolebinding(name, cluster)
                if existing_clusterrolebinding:
                    print(f"{bc.YELLOW}  :!:{cluster}:  ClusterRoleBinding {bc.ENDC}'{name}' {bc.YELLOW}already exists. Skipping creation.{bc.ENDC}")
                else:
                    self.create_clusterrolebinding(name, cluster_role, cluster)
                    print(f"{bc.GREEN}  :+:{cluster}:  ClusterRoleBinding {bc.ENDC}'{name}' {bc.GREEN}created successfully.{bc.ENDC}")
