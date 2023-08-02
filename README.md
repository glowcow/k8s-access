# Kubernetes RBAC Management Tool

## Description

Kubernetes RBAC Management Tool - This application allows you to create users, assign them roles at the cluster and namespace levels.

## Version

![Version: 1.2.0](https://img.shields.io/badge/Version-1.2.0-informational?style=flat)

## Dependencies

* Python 3.6+
* Kubernetes Python Client
* cryptography
* Jinja2

## Installation

1. Clone the repository with the tool
2. Install the required dependencies using the command `pip install -r requirements.txt`

## Usage

```
app.py [-h] [--cluster CLUSTER] [--namespace NAMESPACE] [--role ROLE] [--rolens ROLENS] [--config CONFIG] user
```

Arguments:

* `user`: Username
* `cluster_or_ns`: Cluster name or a comma-separated list of namespaces
* `-r, --role`: ClusterRole
* `-rn, --rolens`: Namespace Role (default: `namespace-admin`)
* `-c, --config`: Path to the configuration file (default: `app.config.yaml`)

## Usage Examples

1. Creating a user and binding a ClusterRole:

```bash
app.py j.doe --cluster dev,prod --role devops
```

2. Creating a Role and RoleBinding at the Namespace level:

```bash
app.py j.doe --cluster dev,prod --namespace test-ns1,test-ns2,test-ns3 --rolens namespace-admin
```

## Usage Examples in GitLab CI/CD

You need to go to CI/CD > Run pipeline and enter the variables:

1. Creating a user and binding a ClusterRole:
* **USER** - Username (e.g. *j.doe*).
* **CLUSTER** - Cluster name from the configuration file (e.g. *prod*).
* **ROLE** - Role name from the configuration file (e.g. *devops*).

Created kube config is stored for 5 minutes in artifacts.

2. Creating a Role and RoleBinding at the Namespace level:
* **USER** - Username (e.g. *j.doe*).
* **CLUSTER** - Cluster name from the configuration file (e.g. *prod*).
* **NS** - Namespace or a comma-separated list of namespaces (e.g. *test-ns1,test-ns2,test-ns3*).
* **RNS** - Role in the namespace (e.g. *namespace-admin*).

## Configuration File

The configuration file is a YAML file containing settings and data about clusters and roles. Example file structure:

```yaml
clusters:
  dev:
    url: "https://cluster-dev:6443"
    ca_data: "<cluster CA cert in base64>"
    cluster_name : "kube-dev"
    cluster_roles:
      devops:
        - cluster-observer
        - devops
  prod:
    url: "https://cluster-prod:6443"
    ca_data: "<cluster CA cert in base64>"
    cluster_name : "kube-prod"
    cluster_roles:
      devops:
        - cluster-observer
        - devops
```

In this example, two clusters (`dev` и `prod`) and the ClusterRole `devops` for each of them.

## Kube config file for the application to work

```context: name:``` should match what is specified in the module ```main.kubeapi``` in the variable ```self.context_pre=```

The default value for this variable: ```self.context_pre = 'k8s-access-'```

By default, the file should be located at ```/app/kube_conf.yaml``` if running inside a Docker container.

If the application is run directly, the default file location should be ```~/.kube/config```

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: <data in base64>
    server: https://cluster-dev:6443
  name: ofd-kube-dev
- cluster:
    certificate-authority-data: <data in base64>
    server: https://cluster-prod:6443
  name: ofd-kube-prod
contexts:
- context:
    cluster: kube-dev
    user: k8s-access-dev
  name: k8s-access-dev
- context:
    cluster: kube-prod
    user: k8s-access-prod
  name: k8s-access-prod
current-context: k8s-access-dev
kind: Config
preferences: {}
users:
- name: k8s-access-dev
  user:
    client-certificate-data: <data in base64>
    client-key-data: 
- name: k8s-access-prod
  user:
    client-certificate-data: <data in base64>
    client-key-data: <data in base64>
```
