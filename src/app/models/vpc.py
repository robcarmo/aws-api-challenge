from dataclasses import dataclass
from typing import List
from enum import Enum


class SubnetType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


@dataclass
class SubnetDefinition:
    name: str
    cidr_block: str
    availability_zone: str
    subnet_type: SubnetType = SubnetType.PRIVATE

    @classmethod
    def from_dict(cls, data: dict) -> "SubnetDefinition":
        return cls(
            name=data["name"],
            cidr_block=data["cidr_block"],
            availability_zone=data["availability_zone"],
            subnet_type=SubnetType(data.get("subnet_type", "private")),
        )


@dataclass
class CreateVpcRequest:
    cidr_block: str
    name: str
    project: str
    environment: str
    subnets: List[SubnetDefinition]

    @classmethod
    def from_dict(cls, data: dict) -> "CreateVpcRequest":
        return cls(
            cidr_block=data["cidr_block"],
            name=data["name"],
            project=data.get("project", "default"),
            environment=data.get("environment", "dev"),
            subnets=[SubnetDefinition.from_dict(s) for s in data.get("subnets", [])],
        )
