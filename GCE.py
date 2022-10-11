import re
import sys
from typing import Any, List
import warnings
import time
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
import paramiko

def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> Any:
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result


def create_instance(
    project_id: str,
    zone: str,
    instance_name: str,
    machine_image: str,
    network_link: str = "global/networks/default",
    external_access: bool = False,
    external_ipv4: str = None,
) -> compute_v1.Instance:
    instance_client = compute_v1.InstancesClient()

     # Use the network interface provided in the network_link argument.
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = network_link
    if external_access:
        access = compute_v1.AccessConfig()
        access.type_ = compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name
        access.name = "External NAT"
        access.network_tier = access.NetworkTier.PREMIUM.name
        if external_ipv4:
            access.nat_i_p = external_ipv4
        network_interface.access_configs = [access]
    # Collect information into the Instance object.
    instance = compute_v1.Instance()
    instance.network_interfaces = [network_interface]
    instance.name = instance_name
    # Prepare the request to insert an instance.
    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project_id
    request.instance_resource = instance
    request.source_machine_image=machine_image 

    # Wait for the create operation to complete.
    print(f"Creating the {instance_name} instance in {zone}...")

    operation = instance_client.insert(request=request)

    wait_for_extended_operation(operation, "instance creation")

    print(f"Instance {instance_name} created.")
    return instance_client.get(project=project_id, zone=zone, instance=instance_name)

#get public ip
def ip_address(instance_name):
    instance_client = compute_v1.InstancesClient()
    dict=instance_client.get(project="gifted-airport-364210",zone="us-central1-a",instance=instance_name)
    return dict.network_interfaces[0].access_configs[0].nat_i_p    
## Run command against your linux VM
def runRemoteShellCommands (host,command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c = client.connect(host,port=22,username='salim_grayaa', key_filename=r'C:\\Users\\salim\\.ssh\\googlessh')
    stdin, stdout, stderr = client.exec_command(command) #assuming is linux
    print(stdout.read().decode())



create_instance("gifted-airport-364210","us-central1-a","backend","projects/gifted-airport-364210/global/machineImages/backend-cloudlab",network_link="global/networks/backend-team9-ip",external_access=True,external_ipv4="34.172.60.162")
while True:
    instance_client = compute_v1.InstancesClient()
    status=instance_client.get(project="gifted-airport-364210",zone="us-central1-a",instance="backend").status
    if status == "RUNNING":
        print("Backend is running")
        break
time.sleep(30)
backend_ip=ip_address("backend")
runRemoteShellCommands (backend_ip,"sudo systemctl start nginx")
runRemoteShellCommands (backend_ip,"sudo systemctl status nginx")
create_instance("gifted-airport-364210","us-central1-a","frontend","projects/gifted-airport-364210/global/machineImages/frontend-cloudlab",external_access=True)
while True:
    instance_client = compute_v1.InstancesClient()
    status=instance_client.get(project="gifted-airport-364210",zone="us-central1-a",instance="frontend").status
    if status == "RUNNING":
        print("frontend is running")
        break
time.sleep(30)
frontend_ip=ip_address("frontend")
runRemoteShellCommands (frontend_ip,"sudo systemctl start apache2")
runRemoteShellCommands (frontend_ip,"sudo systemctl status apache2")
print("you can check our website:",frontend_ip)



