#!/usr/bin/env python3

from kubernetes import client
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from pathlib import Path
from main.configbuilder import KubeConfigBuilder
from main.colors import bc
from main.kubeapi import KubeApi
import base64, datetime, time

class KubernetesUserCreator:

    def __init__(self, app_config, username, clusters, cluster_role):
        self.app_config = app_config
        self.clusters = clusters
        self.cluster_role = cluster_role
        self.username = username
        self.csr_name = f"{username}-csr"
        self.context_names = {cluster: f"{self.username}-{cluster}" for cluster in self.clusters}

        self.k8s = KubeApi(self.clusters)
        self.kube_clients = self.k8s.kube_clients_certs()

    def generate_private_key(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

    def generate_csr(self):
        csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, self.username),
        ])).sign(self.private_key, hashes.SHA256(), default_backend())

        self.csr_pem = csr.public_bytes(serialization.Encoding.PEM)

    def create_csr(self, cluster):
        kube_client = self.kube_clients[cluster]
        csr_metadata = client.V1ObjectMeta(name=self.csr_name)
        csr_body = client.V1CertificateSigningRequest(
            metadata=csr_metadata,
            spec={
                "request": base64.b64encode(self.csr_pem).decode("utf-8"),
                "usages": ["digital signature", "key encipherment", "client auth"],
                "signerName": "kubernetes.io/kube-apiserver-client",
            }
        )
        return kube_client.create_certificate_signing_request(body=csr_body)

    def approve_csr(self, cluster, csr):
        kube_client = self.kube_clients[cluster]
        approval_condition = client.V1CertificateSigningRequestCondition(
            type="Approved",
            status="True",
            reason="UserCreation",
            message="Approved by script",
            last_transition_time=datetime.datetime.now(datetime.timezone.utc)
        )
        approval_patch = {
            "metadata": {
                "name": csr.metadata.name
            },
            "status": {
                "conditions": [approval_condition]
            }
        }
        return kube_client.patch_certificate_signing_request_approval(
            name=csr.metadata.name, body=approval_patch)

    def retrieve_signed_certificate(self, cluster, approved_csr):
        kube_client = self.kube_clients[cluster]
        time.sleep(3)
        signed_csr = kube_client.read_certificate_signing_request_status(name=approved_csr.metadata.name)
        return base64.b64decode(signed_csr.status.certificate)

    def save_credentials(self, signed_certificate_pem, cluster):
        key_file = Path(f"generated/{self.username}-{cluster}.key")
        key_file.parent.mkdir(exist_ok=True, parents=True)
        key_file.write_bytes(self.private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            ))

        cert_file = Path(f"generated/{self.username}-{cluster}.crt")
        cert_file.parent.mkdir(exist_ok=True, parents=True)
        cert_file.write_bytes(signed_certificate_pem)

    def check_existing_csr(self, cluster):
        kube_client = self.kube_clients[cluster]
        existing_csr = None
        csr_list = kube_client.list_certificate_signing_request()
        for csr in csr_list.items:
            if csr.metadata.name == self.csr_name:
                existing_csr = csr
                break

        return existing_csr

    def delete_csr_if_exists(self, cluster):
        existing_csr = self.check_existing_csr(cluster)

        if existing_csr:
            print(f"{bc.RED}  :-:{cluster}:  Deleting existing CertificateSigningRequest:{bc.ENDC} {self.csr_name}")
            kube_client = self.kube_clients[cluster]
            kube_client.delete_certificate_signing_request(name=self.csr_name)

    def create_kubeconfig(self):
        cert_files = {cluster: f"generated/{self.username}-{cluster}.crt" for cluster in self.clusters}
        key_files = {cluster: f"generated/{self.username}-{cluster}.key" for cluster in self.clusters}

        context_data = [
            {
                "name": context_name,
                "cluster_name": self.app_config["clusters"][cluster]["cluster_name"],
                "username": self.username,
                "user": f"{self.username}-{cluster}",
                "client_cert_data": base64.b64encode(open(cert_files[cluster], "rb").read()).decode("utf-8"),
                "client_key_data": base64.b64encode(open(key_files[cluster], "rb").read()).decode("utf-8")
            }
            for cluster, context_name in self.context_names.items()
        ]

        kubeconfig_builder = KubeConfigBuilder()

        clusters_config = self.app_config["clusters"]
        chosen_clusters_config = {}

        for cl in self.clusters:
            if cl in clusters_config:
                chosen_clusters_config[cl] = clusters_config[cl]

        kubeconfig_builder.save_kubeconfig(
            "generated/config",
            context_data=context_data,
            clusters=self.app_config["clusters"],
            current_context=list(self.context_names.values())[0]
        )

    def create_user(self):
        self.generate_private_key()
        self.generate_csr()
    
        for cluster in self.clusters:
            self.delete_csr_if_exists(cluster)
            created_csr = self.create_csr(cluster)
            print(f"{bc.GREEN}  :+:{cluster}:  Created CertificateSigningRequest:{bc.ENDC} {created_csr.metadata.name}")
    
            approved_csr = self.approve_csr(cluster, created_csr)
            print(f"{bc.GREEN}  :+:{cluster}:  Approved CertificateSigningRequest: {bc.ENDC}{approved_csr.metadata.name}")
            signed_certificate_pem = self.retrieve_signed_certificate(cluster, approved_csr)
            self.save_credentials(signed_certificate_pem, cluster)
            print(f"{bc.GREEN}  :+:{cluster}:  Private key and signed certificate saved.{bc.ENDC}")
    
        self.create_kubeconfig()
