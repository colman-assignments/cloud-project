import pulumi_aws as aws

import config


def configure(
    vpc: aws.ec2.Vpc,
    instances: list[aws.ec2.Instance],
    public_subnets: list[aws.ec2.Subnet],
    security_group: aws.ec2.SecurityGroup,
) -> aws.lb.LoadBalancer:
    alb = aws.lb.LoadBalancer(
        f"{config.project_name}-alb",
        load_balancer_type="application",
        subnets=[subnet.id for subnet in public_subnets],
        security_groups=[security_group.id],
        enable_deletion_protection=False,
    )

    target_group = aws.lb.TargetGroup(
        "http-tg",
        port=80,
        protocol="HTTP",
        vpc_id=vpc.id,
        health_check=aws.lb.TargetGroupHealthCheckArgs(
            interval=5,
            healthy_threshold=5,
            unhealthy_threshold=2,
            timeout=3,
        ),
    )

    for i, instance in enumerate(instances):
        aws.lb.TargetGroupAttachment(
            f"instance-{i}-tg-attachment",
            target_group_arn=target_group.arn,
            target_id=instance.id,
        )

    aws.lb.Listener(
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

    return alb
