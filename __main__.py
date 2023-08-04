import pulumi
import pulumi_command as command
import pulumi_aws as aws

config = pulumi.Config()
public_key_path = config.require("publicKeyPath")
private_key_path = config.require("privateKeyPath")
public_key = open(public_key_path).read()

availability_zones = aws.get_availability_zones()
aws_linux_ami = aws.ec2.get_ami(
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["amzn2-ami-hvm-*-x86_64-ebs"],
        )
    ],
    most_recent=True,
)

project_name = "cloud-project"
number_of_instances = 2

security_group = aws.ec2.SecurityGroup(
    f"{project_name}-sg",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
)

keypair = aws.ec2.KeyPair(f"{project_name}-keypair", public_key=public_key)

instances = [
    aws.ec2.Instance(
        f"{project_name}-instance-{i}",
        instance_type="t2.micro",
        ami=aws_linux_ami.id,
        vpc_security_group_ids=[security_group.id],
        key_name=keypair.id,
    )
    for i in range(number_of_instances)
]

default_vpc = aws.ec2.DefaultVpc("default-vpc")
default_subnets = [
    aws.ec2.DefaultSubnet(f"default-{az}", availability_zone=az)
    for az in availability_zones.names
]

alb = aws.lb.LoadBalancer(
    f"{project_name}-alb",
    load_balancer_type="application",
    subnets=[subnet.id for subnet in default_subnets],
    security_groups=[security_group.id],
    enable_deletion_protection=False,
)

target_group = aws.lb.TargetGroup(
    "http-tg", port=80, protocol="HTTP", vpc_id=default_vpc.id
)

for i, instance in enumerate(instances):
    aws.lb.TargetGroupAttachment(
        f"instance-{i}-tg-attachment",
        target_group_arn=target_group.arn,
        target_id=instance.id,
    )


listener = aws.lb.Listener(
    "alb-listener",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[
        {
            "type": "forward",
            "target_group_arn": target_group.arn,
        }
    ],
)


for i, instance in enumerate(instances):
    eip = aws.ec2.Eip(f"eip-{i}", instance=instance.id)

    play_ansible_playbook_cmd = command.local.Command(
        f"configure-ec2-playbook-{i}",
        create=eip.public_ip.apply(
            lambda public_ip: f"""\
    ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook \
    -u ec2-user \
    -i '{public_ip},' \
    --private-key {private_key_path} \
    playbooks/configure_ec2.yaml"""
        ),
        opts=pulumi.ResourceOptions(depends_on=[alb]),
    )
