import pulumi
import pulumi_aws as aws

import config


subnet_config = {
    "public": [
        {
            "availability_zone": "eu-central-1a",
            "cidr_block": "10.0.0.0/20",
        },
        {
            "availability_zone": "eu-central-1b",
            "cidr_block": "10.0.16.0/20",
        },
    ],
    "private": [
        {
            "availability_zone": "eu-central-1c",
            "cidr_block": "10.0.128.0/20",
        }
    ],
}


def configure() -> tuple[aws.ec2.Vpc, list[aws.ec2.Subnet], list[aws.ec2.Subnet]]:
    vpc = aws.ec2.Vpc(
        f"{config.project_name}-vpc",
        cidr_block="10.0.0.0/16",
    )

    public_subnets = [
        aws.ec2.Subnet(
            f"{subnet['availability_zone']}-public-subnet",
            vpc_id=vpc.id,
            availability_zone=subnet["availability_zone"],
            map_public_ip_on_launch=True,
            cidr_block=subnet["cidr_block"],
        )
        for subnet in subnet_config["public"]
    ]

    private_subnets = [
        aws.ec2.Subnet(
            f"{subnet['availability_zone']}-private-subnet",
            vpc_id=vpc.id,
            availability_zone=subnet["availability_zone"],
            map_public_ip_on_launch=False,
            cidr_block=subnet["cidr_block"],
        )
        for subnet in subnet_config["private"]
    ]

    igw = aws.ec2.InternetGateway(
        f"{config.project_name}-igw",
        vpc_id=vpc.id,
    )

    aws.ec2.Route(
        "igw-route",
        route_table_id=vpc.default_route_table_id,
        gateway_id=igw.id,
        destination_cidr_block="0.0.0.0/0",
    )

    [
        aws.ec2.RouteTableAssociation(
            f"{config.project_name}-subnet-route-{i}",
            route_table_id=vpc.default_route_table_id,
            subnet_id=subnet.id,
            opts=pulumi.ResourceOptions(depends_on=[*public_subnets, *private_subnets]),
        )
        for i, subnet in enumerate(public_subnets)
    ]

    return (vpc, public_subnets, private_subnets)
