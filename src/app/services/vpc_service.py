import boto3
from typing import List, Dict, Any
from ..models.vpc import SubnetDefinition, SubnetType


class VpcService:
    def __init__(self, region: str = None):
        self.ec2 = boto3.client("ec2", region_name=region) if region else boto3.client("ec2")

    def create_vpc(self, cidr_block: str, name: str, project: str, environment: str) -> Dict[str, Any]:
        response = self.ec2.create_vpc(
            CidrBlock=cidr_block,
            TagSpecifications=[
                {
                    "ResourceType": "vpc",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                        {"Key": "Project", "Value": project},
                        {"Key": "Environment", "Value": environment},
                        {"Key": "ManagedBy", "Value": "vpc-api"},
                    ],
                }
            ],
        )
        vpc = response["Vpc"]
        vpc_id = vpc["VpcId"]

        self.ec2.get_waiter("vpc_available").wait(VpcIds=[vpc_id])
        self.ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
        self.ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})

        return {"vpc_id": vpc_id, "cidr_block": vpc["CidrBlock"], "state": vpc["State"]}

    def create_subnet(self, vpc_id: str, subnet_def: SubnetDefinition, project: str, environment: str) -> Dict[str, Any]:
        response = self.ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=subnet_def.cidr_block,
            AvailabilityZone=subnet_def.availability_zone,
            TagSpecifications=[
                {
                    "ResourceType": "subnet",
                    "Tags": [
                        {"Key": "Name", "Value": subnet_def.name},
                        {"Key": "Project", "Value": project},
                        {"Key": "Environment", "Value": environment},
                        {"Key": "SubnetType", "Value": subnet_def.subnet_type.value},
                        {"Key": "ManagedBy", "Value": "vpc-api"},
                    ],
                }
            ],
        )
        subnet = response["Subnet"]
        subnet_id = subnet["SubnetId"]

        if subnet_def.subnet_type == SubnetType.PUBLIC:
            self.ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={"Value": True})

        return {
            "subnet_id": subnet_id,
            "cidr_block": subnet["CidrBlock"],
            "availability_zone": subnet["AvailabilityZone"],
            "map_public_ip_on_launch": subnet_def.subnet_type == SubnetType.PUBLIC,
        }

    def create_vpc_with_subnets(
        self, cidr_block: str, name: str, project: str, environment: str, subnet_definitions: List[SubnetDefinition]
    ) -> Dict[str, Any]:
        vpc_result = self.create_vpc(cidr_block, name, project, environment)
        vpc_id = vpc_result["vpc_id"]

        subnets = []
        for subnet_def in subnet_definitions:
            subnet_result = self.create_subnet(vpc_id, subnet_def, project, environment)
            subnets.append({
                "subnet_id": subnet_result["subnet_id"],
                "name": subnet_def.name,
                "cidr_block": subnet_result["cidr_block"],
                "availability_zone": subnet_result["availability_zone"],
                "subnet_type": subnet_def.subnet_type.value,
                "map_public_ip_on_launch": subnet_result["map_public_ip_on_launch"],
            })

        return {
            "vpc_id": vpc_id,
            "cidr_block": cidr_block,
            "name": name,
            "project": project,
            "environment": environment,
            "subnets": subnets,
        }

    def delete_vpc(self, vpc_id: str) -> None:
        subnets = self.ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
        for subnet in subnets:
            self.ec2.delete_subnet(SubnetId=subnet["SubnetId"])

        igws = self.ec2.describe_internet_gateways(Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}])["InternetGateways"]
        for igw in igws:
            self.ec2.detach_internet_gateway(InternetGatewayId=igw["InternetGatewayId"], VpcId=vpc_id)
            self.ec2.delete_internet_gateway(InternetGatewayId=igw["InternetGatewayId"])

        self.ec2.delete_vpc(VpcId=vpc_id)

    def get_vpc_live_data(self, vpc_id: str) -> Dict[str, Any]:
        try:
            vpcs = self.ec2.describe_vpcs(VpcIds=[vpc_id])["Vpcs"]
            if not vpcs:
                return None
            vpc = vpcs[0]
            subnets = self.ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
            return {
                "vpc_id": vpc["VpcId"],
                "cidr_block": vpc["CidrBlock"],
                "state": vpc["State"],
                "subnets": [
                    {
                        "subnet_id": s["SubnetId"],
                        "cidr_block": s["CidrBlock"],
                        "availability_zone": s["AvailabilityZone"],
                        "state": s["State"],
                    }
                    for s in subnets
                ],
            }
        except Exception:
            return None
