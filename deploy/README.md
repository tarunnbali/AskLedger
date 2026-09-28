# deploy/

Kubernetes delivery (phase 2): the Helm chart (deployment, service, ingress,
HPA, probes on `/health` and `/ready`, resource limits) and the Argo CD
application that watches this folder. CI will bump the image tag and prompt
version here; Argo CD syncs the cluster.

Empty until phase 2.
