#!/usr/bin/env python3

from pathlib import Path
from main.colors import bc
import jinja2

class KubeConfigBuilder:

    def __init__(self):
        pass

    def build_kubeconfig(self, context_data, clusters, current_context):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        t = env.get_template("kube_config.j2")
        kubeconfig_content = t.render(
            clusters=[{"ca_data": cluster["ca_data"], "server": cluster["url"], "name": cluster["cluster_name"]} for cluster in clusters.values()],
            contexts=context_data,
            current_context=current_context,
            users=[{
                "user": context["user"],
                "client_cert_data": context["client_cert_data"],
                "client_key_data": context["client_key_data"]
            } for context in context_data]
        )
        return kubeconfig_content

    def save_kubeconfig(self, file_path, context_data, clusters, current_context):
        kubeconfig_content = self.build_kubeconfig(context_data, clusters, current_context)
        f = Path(file_path)
        f.parent.mkdir(exist_ok=True, parents=True)
        f.write_text(kubeconfig_content)
        print(f"{bc.GREEN}  :+:  Kubeconfig saved to:{bc.ENDC} {file_path}")
