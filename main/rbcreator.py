#!/usr/bin/env python3

from kubernetes import client
from kubernetes.client.rest import ApiException
from main.colors import bc
from main.kubeapi import KubeApi
import yaml

class K8sRoleAndRoleBinding:

    def __init__(self, user, clusters, namespace, role):
        self.namespace = namespace
        self.user = user
        self.clusters = clusters
        self.role_name = role
        self.role_binding_name = f'{self.role_name}:{user}'

        self.k8s = KubeApi(self.clusters)
        self.kube_clients = self.k8s.kube_clients_rbac()
        self.kube_clients_core = self.k8s.kube_clients_core()

    def namespace_exists(self, cluster, namespace):
        kube_client_core = self.kube_clients_core[cluster]
        try:
            kube_client_core.read_namespace(namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                print(f"{bc.YELLOW}  :!:{cluster}:  Namespace {bc.ENDC}'{namespace}'{bc.YELLOW} does not exist, skipping role creation{bc.ENDC}")
                return False
            else:
                raise

    def load_role_template(self, namespace):
        with open(f'templates/{self.role_name}.yaml', 'r') as f:
            role_data = yaml.safe_load(f)

        role_data['metadata']['namespace'] = namespace
        metadata = role_data['metadata']

        rules = [client.V1PolicyRule(api_groups=rule['apiGroups'], resources=rule['resources'], verbs=rule['verbs'])
                 for rule in role_data['rules']]

        return metadata, rules

    def create_role(self):
        for cluster in self.clusters:
             for ns in self.namespace:
                if self.namespace_exists(cluster, ns):
                    try:
                        kube_client = self.kube_clients[cluster]
                        metadata, rules = self.load_role_template(ns)
                        role = client.V1Role(metadata=client.V1ObjectMeta(**metadata), rules=rules)
                        kube_client.create_namespaced_role(ns, role)
                        print(f"{bc.GREEN}  :+:{cluster}:  Role {bc.ENDC}'{self.role_name}' {bc.GREEN}created in namespace {bc.ENDC}'{ns}'")
                    except ApiException as e:
                        if e.status == 409:
                            print(f"{bc.YELLOW}  :!:{cluster}:  Role {bc.ENDC}'{self.role_name}' {bc.YELLOW}already exists in namespace {bc.ENDC}'{ns}'")
                        else:
                            raise

    def create_role_binding(self):
        role_binding_body = client.V1RoleBinding(
            metadata=client.V1ObjectMeta(name=self.role_binding_name),
            subjects=[
                client.V1Subject(kind="User", name=self.user)
            ],
            role_ref=client.V1RoleRef(
                api_group="rbac.authorization.k8s.io",
                kind="Role",
                name=self.role_name
            )
        )
        for cluster in self.clusters:
            for ns in self.namespace:
                if self.namespace_exists(cluster, ns):
                    try:
                        kube_client = self.kube_clients[cluster]
                        kube_client.create_namespaced_role_binding(ns, role_binding_body)
                        print(f"{bc.GREEN}  :+:{cluster}:  RoleBinding {bc.ENDC}'{self.role_binding_name}' {bc.GREEN}created for user{bc.ENDC} '{self.user}' {bc.GREEN}in namespace{bc.ENDC} '{ns}'")
                    except ApiException as e:
                        if e.status == 409:
                            print(f"{bc.YELLOW}  :!:{cluster}:  RoleBinding {bc.ENDC}'{self.role_binding_name}' {bc.YELLOW}already exists in namespace {bc.ENDC}'{ns}'")
                        else:
                            raise
