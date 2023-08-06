import pulumi
import pulumi_aws as aws

import config

import modules.network as network
import modules.ec2 as ec2
import modules.rds as rds
import modules.load_balancer as load_balancer

vpc, public_subnets, private_subnets = network.configure()

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

security_group = aws.ec2.SecurityGroup(
    f"{config.project_name}-sg",
    vpc_id=vpc.id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 8001,
            "to_port": 8001,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

keypair = aws.ec2.KeyPair(
    f"{config.project_name}-keypair", public_key=config.public_key
)

instances = ec2.deploy_machines(
    aws_linux_ami=aws_linux_ami,
    security_group=security_group,
    keypair=keypair,
    public_subnets=public_subnets,
)

rds_instance = rds.configure(vpc=vpc, subnets=private_subnets)

alb = load_balancer.configure(
    vpc=vpc,
    instances=instances,
    public_subnets=public_subnets,
    security_group=security_group,
)

ec2.configure_machines(instances=instances, alb=alb, rds=rds_instance)

pulumi.export("url", alb.dns_name)
