import pulumi_aws as aws

import config


def configure(
    vpc: aws.ec2.Vpc, subnets: list[aws.ec2.Subnet]
) -> aws.rds.Instance:
    rds_subnet_grp = aws.rds.SubnetGroup(
        "rds-subnet-grp", subnet_ids=[subnet.id for subnet in subnets]
    )

    security_group = aws.ec2.SecurityGroup(
        f"{config.project_name}-pg-sg",
        vpc_id=vpc.id,
        ingress=[
            {
                "protocol": "tcp",
                "from_port": 5432,
                "to_port": 5432,
                "cidr_blocks": ["0.0.0.0/0"],
            }
        ],
    )

    rds = aws.rds.Instance(
        f"{config.project_name}-rds",
        allocated_storage=10,
        db_name="database1",
        engine="postgres",
        engine_version="15.3",
        instance_class="db.t3.micro",
        username="postgres",
        password="0Password",
        skip_final_snapshot=True,
        db_subnet_group_name=rds_subnet_grp.id,
        vpc_security_group_ids=[security_group.id],
        publicly_accessible=True,
    )

    return rds
