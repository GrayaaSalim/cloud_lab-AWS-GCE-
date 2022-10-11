import boto3
import paramiko

## EC2 instance boto3
def create_instance(ImageId):
    print("Create AWS instances..")
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    instances = ec2_client.run_instances(
        ImageId=ImageId,
        MinCount=1, 
        MaxCount=1, 
        InstanceType="t2.micro",
        KeyName="cloud_lecture_master",
        SecurityGroups=["rds-ec2-4","ec2-rds-3","launch-wizard-24","ec2-rds-2","ec2-rds-1"],
        Placement={"AvailabilityZone":"us-east-1e"}
    )
    return instances["Instances"][0]["InstanceId"]

## allocate elastic ip for the backend
def allocate_ip_address(instance_id):
    ec2Client = boto3.client('ec2')
    ec2Client.associate_address(
    InstanceId = instance_id,
    AllocationId = "eipalloc-06efc29f9f476cdda")

## How to get the public IP for a running EC2 instance
def get_public_ip(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")
    for reservation in reservations:
        for instance in reservation['Instances']:
            print(instance.get("PublicIpAddress"))


## Run command against your linux VM
def runRemoteShellCommands (instance_id,command):
    ec2 = boto3.resource('ec2')
    instance=ec2.Instance(instance_id)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file('D:\hes-so master\AWS\cloud_lecture_master.pem')
    ssh.connect(instance.public_dns_name,username='ec2-user',pkey=privkey)
    stdin, stdout, stderr = ssh.exec_command(command)
    stdin.flush()
    data = stdout.read().splitlines()
    for line in data:
        print(line.decode())
        ssh.close()
    


print("###########################Backend###########################")
BackendInstanceID=create_instance("ami-043b2a4a021861bbb")
#BackendInstanceID="i-06874a101b71dd00a"
print(BackendInstanceID)
ec2 = boto3.resource('ec2')
instance=ec2.Instance(BackendInstanceID)
instance.wait_until_running('self',Filters=[{'Name':'instance-state-name','Values':['running']}])
print ("instance is now running")
runRemoteShellCommands(BackendInstanceID,'sudo systemctl start nginx')
runRemoteShellCommands(BackendInstanceID,'sudo systemctl status nginx')
allocate_ip_address(BackendInstanceID)
print("###########################Frontend###########################")
FrontendInstanceID=create_instance("ami-03ddc45883cc439bf")
print(FrontendInstanceID)
ec2 = boto3.resource('ec2')
instance=ec2.Instance(FrontendInstanceID)
instance.wait_until_running('self',Filters=[{'Name':'instance-state-name','Values':['running']}])
print ("instance is now running")
runRemoteShellCommands(FrontendInstanceID,'sudo systemctl start httpd')
runRemoteShellCommands(FrontendInstanceID,'sudo systemctl status httpd')
get_public_ip(FrontendInstanceID)

