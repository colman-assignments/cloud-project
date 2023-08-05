import pulumi

config = pulumi.Config()

project_name = config.require("projectName")
public_key_path = config.require("publicKeyPath")
private_key_path = config.require("privateKeyPath")

public_key = open(public_key_path).read()
