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

    target_groups = [
        aws.lb.TargetGroup(
            f"port-{port}-tg",
            port=port,
            protocol="HTTP",
            vpc_id=vpc.id,
            health_check=aws.lb.TargetGroupHealthCheckArgs(
                interval=5,
                healthy_threshold=5,
                unhealthy_threshold=2,
                timeout=3,
            ),
        )
        for port in [80, 8001]
    ]

    for i, instance in enumerate(instances):
        for j, target_group in enumerate(target_groups):
            aws.lb.TargetGroupAttachment(
                f"instance-{i}-{j}-tg-attachment",
                target_group_arn=target_group.arn,
                target_id=instance.id,
            )

    for i, target_group in enumerate(target_groups):
        aws.lb.Listener(
            f"alb-{i}-listener",
            load_balancer_arn=alb.arn,
            port=target_group.port,
            default_actions=[
                {
                    "type": "forward",
                    "target_group_arn": target_group.arn,
                }
            ],
        )

    return alb
