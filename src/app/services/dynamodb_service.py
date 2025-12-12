import boto3
import os
from typing import List, Optional, Dict, Any
from datetime import datetime


class DynamoDBService:
    def __init__(self, table_name: str = None):
        self.table_name = table_name or os.environ.get("DYNAMODB_TABLE", "vpc-api-resources")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def save_vpc(self, vpc_data: Dict[str, Any]) -> None:
        item = {
            "pk": f"VPC#{vpc_data['vpc_id']}",
            "sk": "METADATA",
            "vpc_id": vpc_data["vpc_id"],
            "cidr_block": vpc_data["cidr_block"],
            "name": vpc_data["name"],
            "project": vpc_data["project"],
            "environment": vpc_data["environment"],
            "subnets": vpc_data["subnets"],
            "created_at": vpc_data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat(),
            "entity_type": "VPC",
        }
        self.table.put_item(Item=item)

    def get_vpc(self, vpc_id: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"pk": f"VPC#{vpc_id}", "sk": "METADATA"})
        item = response.get("Item")
        if not item:
            return None
        return {
            "vpc_id": item["vpc_id"],
            "cidr_block": item["cidr_block"],
            "name": item["name"],
            "project": item["project"],
            "environment": item["environment"],
            "subnets": item.get("subnets", []),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }

    def list_vpcs(self) -> List[Dict[str, Any]]:
        response = self.table.scan(
            FilterExpression="entity_type = :et",
            ExpressionAttributeValues={":et": "VPC"},
        )
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = self.table.scan(
                FilterExpression="entity_type = :et",
                ExpressionAttributeValues={":et": "VPC"},
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        return [
            {
                "vpc_id": item["vpc_id"],
                "cidr_block": item["cidr_block"],
                "name": item["name"],
                "project": item["project"],
                "environment": item["environment"],
                "subnets": item.get("subnets", []),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            }
            for item in items
        ]

    def delete_vpc(self, vpc_id: str) -> bool:
        try:
            self.table.delete_item(Key={"pk": f"VPC#{vpc_id}", "sk": "METADATA"})
            return True
        except Exception:
            return False
