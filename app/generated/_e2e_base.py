# Generated from contract/app.pkl via contract-toolkit. DO NOT EDIT.
# Regenerate with: pkl eval -m . contract/app.pkl
from application_sdk.testing.e2e import BaseE2ETest


class HelloWorldGeneratedE2EBase(BaseE2ETest):
    connector_short_name = "hello-world"
    argo_package_name = "@atlan/hello-world"
    argo_template_name = "atlan-hello-world"
    app_service_url = "http://hello-world.hello-world-app.svc.cluster.local"
