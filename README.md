# Kubernetes Role-Patcher

## Target

If you want to have your cluster dev not to have certain mess around system-critical
Kubernetes namespaces like `kube-system`, you need to subtract his rights.
This is not possible in RBAC, so can't use one ClusterRole but need to use RoleBindings
for every single namespace but not `kube-system`.

This (Containerizable) Python-Script using the Kubernetes API will patch the rights on the 
fly for every current and future to-be-created namespace with read+write rights, but
only allow reading on the `kube-system` namespace.

## Usage

First, change the target user context's name:
```python
# The user for which to create the Role and RoleBinding
TARGET_USER = "YOUR_USER"
```

Then, if you want to containerize the script and manage it within Kubernetes' ecosystem:

```bash
docker build -t kubernetes-role-patcher:latest .
docker push <url>
```

After that, download and pull as you like (e.g. Terraform, Helm, plain Kubernetes).
You may need to manage this Container's rights with other Kubernetes resources,
e.g. clusterwide role management capabilities.