import json
import logging
from datetime import datetime
from typing import Dict, Any

from app.services.vpc_service import VpcService
from app.services.dynamodb_service import DynamoDBService
from app.models.vpc import CreateVpcRequest

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _response(status_code: int, body: Any) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
        },
        "body": json.dumps(body),
    }


def create_vpc(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        body = json.loads(event.get("body", "{}") or "{}")
        
        for field in ["cidr_block", "name"]:
            if field not in body:
                return _response(400, {"error": f"Missing required field: {field}"})

        request = CreateVpcRequest.from_dict(body)
        result = VpcService().create_vpc_with_subnets(
            cidr_block=request.cidr_block,
            name=request.name,
            project=request.project,
            environment=request.environment,
            subnet_definitions=request.subnets,
        )
        result["created_at"] = datetime.utcnow().isoformat()
        DynamoDBService().save_vpc(result)
        
        return _response(201, result)
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON"})
    except Exception as e:
        logger.error(f"Error creating VPC: {e}", exc_info=True)
        return _response(500, {"error": str(e)})


def get_vpc(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        vpc_id = (event.get("pathParameters") or {}).get("vpc_id")
        if not vpc_id:
            return _response(400, {"error": "Missing vpc_id"})

        vpc_data = DynamoDBService().get_vpc(vpc_id)
        if not vpc_data:
            return _response(404, {"error": f"VPC {vpc_id} not found"})

        params = event.get("queryStringParameters") or {}
        if params.get("include_live") == "true":
            live = VpcService().get_vpc_live_data(vpc_id)
            if live:
                vpc_data["live_data"] = live

        return _response(200, vpc_data)
    except Exception as e:
        logger.error(f"Error getting VPC: {e}", exc_info=True)
        return _response(500, {"error": str(e)})


def list_vpcs(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        vpcs = DynamoDBService().list_vpcs()
        return _response(200, {"vpcs": vpcs, "count": len(vpcs)})
    except Exception as e:
        logger.error(f"Error listing VPCs: {e}", exc_info=True)
        return _response(500, {"error": str(e)})


def delete_vpc(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        vpc_id = (event.get("pathParameters") or {}).get("vpc_id")
        if not vpc_id:
            return _response(400, {"error": "Missing vpc_id"})

        db = DynamoDBService()
        if not db.get_vpc(vpc_id):
            return _response(404, {"error": f"VPC {vpc_id} not found"})

        VpcService().delete_vpc(vpc_id)
        db.delete_vpc(vpc_id)
        
        return _response(200, {"message": f"VPC {vpc_id} deleted"})
    except Exception as e:
        logger.error(f"Error deleting VPC: {e}", exc_info=True)
        return _response(500, {"error": str(e)})


def health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return _response(200, {"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
