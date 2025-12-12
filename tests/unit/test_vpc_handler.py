import pytest
import json
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from app.handlers.vpc_handler import create_vpc, get_vpc, list_vpcs, health_check
from app.models.vpc import SubnetDefinition, SubnetType, CreateVpcRequest


class TestVpcHandler:
    @patch('app.handlers.vpc_handler.DynamoDBService')
    @patch('app.handlers.vpc_handler.VpcService')
    def test_create_vpc_success(self, mock_vpc_svc, mock_db_svc):
        mock_vpc_svc.return_value.create_vpc_with_subnets.return_value = {
            "vpc_id": "vpc-123", "cidr_block": "10.0.0.0/16", "name": "test",
            "project": "test", "environment": "dev", "subnets": []
        }
        event = {"body": json.dumps({"cidr_block": "10.0.0.0/16", "name": "test"})}
        response = create_vpc(event, None)
        assert response["statusCode"] == 201
        assert json.loads(response["body"])["vpc_id"] == "vpc-123"

    def test_create_vpc_missing_field(self):
        response = create_vpc({"body": json.dumps({"name": "test"})}, None)
        assert response["statusCode"] == 400

    @patch('app.handlers.vpc_handler.DynamoDBService')
    def test_get_vpc_success(self, mock_db_svc):
        mock_db_svc.return_value.get_vpc.return_value = {"vpc_id": "vpc-123", "name": "test"}
        response = get_vpc({"pathParameters": {"vpc_id": "vpc-123"}}, None)
        assert response["statusCode"] == 200

    @patch('app.handlers.vpc_handler.DynamoDBService')
    def test_get_vpc_not_found(self, mock_db_svc):
        mock_db_svc.return_value.get_vpc.return_value = None
        response = get_vpc({"pathParameters": {"vpc_id": "vpc-xxx"}}, None)
        assert response["statusCode"] == 404

    @patch('app.handlers.vpc_handler.DynamoDBService')
    def test_list_vpcs(self, mock_db_svc):
        mock_db_svc.return_value.list_vpcs.return_value = [{"vpc_id": "vpc-1"}]
        response = list_vpcs({}, None)
        assert response["statusCode"] == 200
        assert json.loads(response["body"])["count"] == 1

    def test_health_check(self):
        response = health_check({}, None)
        assert response["statusCode"] == 200


class TestModels:
    def test_subnet_definition(self):
        s = SubnetDefinition.from_dict({"name": "pub", "cidr_block": "10.0.1.0/24", 
                                        "availability_zone": "us-east-1a", "subnet_type": "public"})
        assert s.subnet_type == SubnetType.PUBLIC

    def test_create_vpc_request(self):
        r = CreateVpcRequest.from_dict({"cidr_block": "10.0.0.0/16", "name": "vpc"})
        assert r.project == "default"
        assert len(r.subnets) == 0
