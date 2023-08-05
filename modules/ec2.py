import pulumi
import pulumi_command as command
import pulumi_aws as aws

import config


def deploy_machines(
    aws_linux_ami: aws.ec2.Ami,
    security_group: aws.ec2.SecurityGroup,
    public_subnets: aws.ec2.Subnet,
    keypair: aws.ec2.KeyPair,
) -> list[aws.ec2.Instance]:
    instances = [
        aws.ec2.Instance(
            f"{config.project_name}-instance-{i}",
            instance_type="t2.micro",
            ami=aws_linux_ami.id,
            vpc_security_group_ids=[security_group.id],
            key_name=keypair.id,
            subnet_id=subnet.id,
        )
        for i, subnet in enumerate(public_subnets)
    ]

    return instances


def configure_machines(instances: list[aws.ec2.Instance], alb: aws.lb.LoadBalancer):
    for i, instance in enumerate(instances):
        eip = aws.ec2.Eip(f"eip-{i}", instance=instance.id)

        command.local.Command(
            f"configure-ec2-playbook-{i}",
            create=eip.public_ip.apply(
                lambda public_ip: f"""\
        ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook \
        -u ec2-user \
        -i '{public_ip},' \
        --private-key {config.private_key_path} \
        playbooks/configure_ec2.yaml"""
            ),
            opts=pulumi.ResourceOptions(depends_on=[alb]),
        )
