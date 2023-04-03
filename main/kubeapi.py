#!/usr/bin/env python3

from kubernetes import client, config

class KubeApi:

    def __init__(self, clusters):
        self.clusters = clusters
        self.context_pre = 'k8s-access-' #should match to context name in kubeconfig
        config.load_kube_config()

    def kube_clients_rbac(self):
        kube_clients = {
            cluster: client.RbacAuthorizationV1Api(api_client=config.new_client_from_config(context=f"{self.context_pre}{cluster}"))
            for cluster in self.clusters
        }
        return kube_clients

    def kube_clients_core(self):
        kube_clients = {
            cluster: client.CoreV1Api(api_client=config.new_client_from_config(context=f"{self.context_pre}{cluster}"))
            for cluster in self.clusters
        }
        return kube_clients

    def kube_clients_certs(self):
        kube_clients = {
            cluster: client.CertificatesV1Api(api_client=config.new_client_from_config(context=f"{self.context_pre}{cluster}"))
            for cluster in self.clusters
        }
        return kube_clients
