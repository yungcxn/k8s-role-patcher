"""
role-patcher

Creates for TARGET_USER a Role and RoleBinding for each namespace and a Role and RoleBinding for kube-system.
The Role and RoleBinding for each namespace will have the following permissions:
- All non-privileged resources (i.e. resources that are not roles, rolebindings, clusterroles, clusterrolebindings)
- Read permissions for roles, rolebindings, clusterroles, clusterrolebindings
The Role and RoleBinding for kube-system will have the following permissions:
- Read permissions for all resources
"""

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

def info_print(msg):
    """
    Prints the given message to the console.

    Parameters:
    msg (str): The message to print.

    Returns:
    None
    """

    print(f"(role-patcher): {msg}")

# The user for which to create the Role and RoleBinding
TARGET_USER = "k8user"

# For non-privileged resources
# For reference see: https://kubernetes.io/docs/reference/access-authn-authz/rbac/#resources
ROLE_RESOURCES = ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
READ_VERBS = ["get", "list", "watch"]

# The name of the ClusterRole for non-privileged resources
CUSTOM_ROLE_NAME = TARGET_USER + "-custom-role"

PROTECTED_NAMESPACES = ["kube-system"]

def role_exists(api_instance, namespace, role_name):
    """
    Returns True if the Role exists, False otherwise.

    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    namespace (str): The namespace of the Role.
    role_name (str): The name of the Role.

    Returns:
    bool: True if the Role exists, False otherwise.
    """

    try:
        api_instance.read_namespaced_role(name=role_name, namespace=namespace)
        return True
    except ApiException as e:
        if e.status == 404:
            return False
        else:
            # Handle other exceptions if needed
            raise

def cluster_role_exists(api_instance, role_name):
    """
    Returns True if the ClusterRole exists, False otherwise.

    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    role_name (str): The name of the ClusterRole.

    Returns:
    bool: True if the ClusterRole exists, False otherwise.
    """

    try:
        api_instance.read_cluster_role(name=role_name)
        return True
    except ApiException as e:
        if e.status == 404:
            return False
        else:
            # Handle other exceptions if needed
            raise

def role_binding_exists(api_instance, namespace, role_binding_name):
    """
    Returns True if the RoleBinding exists, False otherwise.

    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    namespace (str): The namespace of the RoleBinding.
    role_binding_name (str): The name of the RoleBinding.

    Returns:
    bool: True if the RoleBinding exists, False otherwise.
    """

    try:
        api_instance.read_namespaced_role_binding(name=role_binding_name, namespace=namespace)
        return True
    except ApiException as e:
        if e.status == 404:
            return False
        else:
            # Handle other exceptions if needed
            raise

def del_role(api_instance, namespace, role_name):
    """
    Deletes the Role with the given name.

    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    namespace (str): The namespace of the Role.
    role_name (str): The name of the Role.

    Returns:
    None
    """

    api_instance.delete_namespaced_role(name=role_name, namespace=namespace)

def del_cluster_role(api_instance, role_name):
    """
    Deletes the ClusterRole with the given name.

    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    role_name (str): The name of the ClusterRole.

    Returns:
    None
    """

    api_instance.delete_cluster_role(name=role_name)

def create_custom_cluster_role(api_instance, non_role_resources):
    """
    Creates a ClusterRole for the given name and permissions.

    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    role_name (str): The name of the ClusterRole.
    non_role_resources (list): The list of non-privileged resources.

    Returns:
    None
    """

    # Define the ClusterRole object, for reference see: https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole
    cluster_role = client.V1ClusterRole(
        api_version="rbac.authorization.k8s.io/v1",
        kind="ClusterRole",
        metadata=client.V1ObjectMeta(name=CUSTOM_ROLE_NAME),
        rules=[
            client.V1PolicyRule(
                api_groups=["*"],
                resources=non_role_resources,
                verbs=["*"]
            ),
            client.V1PolicyRule(
                api_groups=["*"],
                resources=ROLE_RESOURCES,
                verbs=READ_VERBS
            )
        ]
    )

    # Create the ClusterRole
    api_instance.create_cluster_role(body=cluster_role)

def create_custom_role_binding(api_instance, ns, role_binding_name, role_name, rkind="Role"):
    """
    Creates a RoleBinding for the given namespace with the given name and permissions.
    
    Parameters:
    api_instance (client.RbacAuthorizationV1Api): The API instance to use.
    ns (str): The namespace of the RoleBinding.
    role_binding_name (str): The name of the RoleBinding.
    role_name (str): The name of the Role.
    rkind (str): The kind of the Role.
    
    Returns:
    None
    """

    # Define the RoleBinding object, for reference see: https://kubernetes.io/docs/reference/access-authn-authz/rbac/#rolebinding-and-clusterrolebinding
    role_binding = client.V1RoleBinding(
        api_version="rbac.authorization.k8s.io/v1",
        kind="RoleBinding",
        metadata=client.V1ObjectMeta(name=role_binding_name, namespace=ns),
        role_ref=client.V1RoleRef(api_group="rbac.authorization.k8s.io", kind=rkind, name=role_name),
        subjects=[client.RbacV1Subject(api_group="", kind="User", name=TARGET_USER)]
    )

    # Create the RoleBinding
    api_instance.create_namespaced_role_binding(namespace=ns, body=role_binding)


def get_resource_list(api_instance_1, api_instance_2, api_instance_3):
    """
    Returns a list of all resources in the cluster.

    Parameters:
    api_instance_1 (client.CoreV1Api): The API instance to use.
    api_instance_2 (client.AppsV1API): The API instance to use.
    api_instance_3 (client.ApiextensionsV1Api): The API instance to use.


    Returns:
    list: A list of all resources in the cluster.
    """

    # Get list of normal resources
    # For reference see: https://kubernetes.io/docs/reference/access-authn-authz/rbac/#resources
    resources = api_instance_1.get_api_resources()
    resources = [resource.name for resource in resources.resources]

    # Get list of app resources
    # For reference see: 
    app_resources = api_instance_2.get_api_resources()
    app_resources = [resource.name for resource in app_resources.resources]
    resources.extend(app_resources)
    
    # Get list of custom resources
    # For reference see: https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
    custom_resources = api_instance_3.list_custom_resource_definition()
    custom_resources = [resource.spec.names.plural for resource in custom_resources.items]
    resources.extend(custom_resources)

    return resources


def get_non_privilege_resource_list(api_instance_1, api_instance_2, app_instance_3):
    """
    Returns a list of all non-privileged resources in the cluster.

    Parameters:
    api_instance_1 (client.CoreV1Api): The API instance to use.
    api_instance_2 (client.AppsV1API): The API instance to use.
    api_instance_3 (client.ApiextensionsV1Api): The API instance to use.

    Returns:
    list: A list of all non-privileged resources in the cluster.
    """

    resources = get_resource_list(api_instance_1, api_instance_2, app_instance_3)
    return list(set(resources) - set(ROLE_RESOURCES))

def main():
    info_print("Starting...")

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    info_print("Configuration loaded...")

    # For basic core api
    core_v1 = client.CoreV1Api()

    # For App API
    apps_v1 = client.AppsV1Api()

    # To list all resources
    api_extensions_api = client.ApiextensionsV1Api()

    # To create roles and rolebindings
    rbac_api = client.RbacAuthorizationV1Api()

    # Watch for namespace events
    w = watch.Watch()

    info_print("Created API instances...")

    #recreate the cluster role for non-ks
    if cluster_role_exists(rbac_api, CUSTOM_ROLE_NAME):
        #delete and recreate the cluster role for non-ks
        info_print(f"Deleting ClusterRole for non-ks...")
        del_cluster_role(rbac_api, CUSTOM_ROLE_NAME)

    info_print(f"Creating ClusterRole for non-ks...")
    create_custom_cluster_role(rbac_api, get_non_privilege_resource_list(core_v1, apps_v1, api_extensions_api))

    # Watch for namespace events
    # For each namespace, create a Role and RoleBinding if they do not exist
    # For the kube-system namespace, create a Role and RoleBinding if they do not exist
    for event in w.stream(core_v1.list_namespace, timeout_seconds=0):
        # Namespace object
        namespace = event['object']
        # Namespace name
        namespace_name = namespace.metadata.name
        event_type = event['type']

        info_print(f"Namespace: {namespace_name}, Event Type: {event_type}")

        # Event type (ADDED, MODIFIED, DELETED)
        if event_type == "DELETED" or event_type == "MODIFIED":
            info_print(f"Skipping...")
            continue

        if not namespace_name in PROTECTED_NAMESPACES:
            info_print(f"Processing {namespace_name} namespace...")
            role_binding_name = f"{namespace_name}-custom-rolebinding"
            if not cluster_role_exists(rbac_api, CUSTOM_ROLE_NAME):
                info_print(f"Creating ClusterRole for non-ks... (since it was deleted)")
                try:
                    create_custom_cluster_role(rbac_api, get_non_privilege_resource_list(core_v1, apps_v1, api_extensions_api))
                except ApiException as e:
                    info_print(f"Error creating ClusterRole for non-ks: {e} at namespace {namespace_name}...")

            if not role_binding_exists(rbac_api, namespace_name, role_binding_name):
                info_print(f"Creating RoleBinding for namespace...")
                # Create RoleBinding for namespace
                try:
                    create_custom_role_binding(rbac_api, namespace_name, role_binding_name, CUSTOM_ROLE_NAME, "ClusterRole")
                except ApiException as e:
                    info_print(f"Error creating RoleBinding for namespace: {e} at namespace {namespace_name}...")


if __name__ == "__main__":
    main()
