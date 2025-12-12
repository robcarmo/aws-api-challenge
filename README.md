# VPC Management API

AWS serverless API for creating and managing VPCs with subnets.

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Client    │────▶│  API Gateway    │────▶│   Lambda    │
│             │     │  (API Key Auth) │     │  Functions  │
└─────────────┘     └─────────────────┘     └──────┬──────┘
                                                   │
                           ┌───────────────────────┼───────────────────────┐
                           │                       │                       │
                           ▼                       ▼                       ▼
                    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
                    │  DynamoDB   │         │    EC2      │         │ CloudWatch  │
                    │  (Storage)  │         │ (VPC/Subnet)│         │   (Logs)    │
                    └─────────────┘         └─────────────┘         └─────────────┘
```

**Services Used:**
- **API Gateway** - REST API with API Key authentication
- **Lambda** - Python 3.11 functions for API logic
- **DynamoDB** - Stores VPC/subnet metadata
- **EC2** - Creates actual VPC and subnet resources
- **IAM** - Least-privilege roles for Lambda

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- Python 3.11+

## Deployment

```bash
cd aws-api-challenge

# Build
sam build

# Deploy (first time - guided)
sam deploy --guided

# Deploy (subsequent)
sam deploy --parameter-overrides ApiKeyValue=your-api-key-min-20-chars
```

During guided deployment, you'll be prompted for:
- **Stack Name**: e.g., `vpc-api-dev`
- **AWS Region**: e.g., `us-east-1`
- **Environment**: `dev`, `staging`, or `prod`
- **ApiKeyValue**: Your API key (minimum 20 characters)

## Authentication

The API uses API Gateway API Keys for authentication. After deployment:

1. Get the API endpoint from CloudFormation outputs
2. Use the API key you provided during deployment
3. Include the key in requests via `x-api-key` header

## API Endpoints

### Health Check
```bash
curl https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/health
```

### Create VPC
```bash
curl -X POST https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/vpcs \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "cidr_block": "10.0.0.0/16",
    "name": "my-vpc",
    "project": "myproject",
    "environment": "dev",
    "subnets": [
      {
        "name": "public-1a",
        "cidr_block": "10.0.1.0/24",
        "availability_zone": "us-east-1a",
        "subnet_type": "public"
      },
      {
        "name": "private-1a",
        "cidr_block": "10.0.10.0/24",
        "availability_zone": "us-east-1a",
        "subnet_type": "private"
      }
    ]
  }'
```

**Response:**
```json
{
  "vpc_id": "vpc-0abc123...",
  "cidr_block": "10.0.0.0/16",
  "name": "my-vpc",
  "project": "myproject",
  "environment": "dev",
  "subnets": [
    {
      "subnet_id": "subnet-0abc...",
      "name": "public-1a",
      "cidr_block": "10.0.1.0/24",
      "availability_zone": "us-east-1a",
      "subnet_type": "public",
      "map_public_ip_on_launch": true
    }
  ],
  "created_at": "2024-01-15T10:30:00.000000"
}
```

### List VPCs
```bash
curl https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/vpcs \
  -H "x-api-key: your-api-key"
```

### Get VPC Details
```bash
curl https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/vpcs/{vpc_id} \
  -H "x-api-key: your-api-key"

# Include live AWS data
curl "https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/vpcs/{vpc_id}?include_live=true" \
  -H "x-api-key: your-api-key"
```

### Delete VPC
```bash
curl -X DELETE https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/vpcs/{vpc_id} \
  -H "x-api-key: your-api-key"
```

## Running Tests

```bash
pip install pytest pytest-mock
pytest tests/ -v
```

## Project Structure

```
aws-api-challenge/
├── src/
│   ├── app/
│   │   ├── handlers/       # Lambda handlers
│   │   │   ├── vpc_handler.py
│   │   │   └── utils.py
│   │   ├── services/       # Business logic
│   │   │   ├── vpc_service.py
│   │   │   └── dynamodb_service.py
│   │   └── models/         # Data models
│   │       └── vpc.py
│   └── __init__.py
├── tests/
│   └── unit/
│       └── test_vpc_handler.py
├── template.yaml           # SAM template
├── requirements.txt
└── README.md
```

## Cleanup

```bash
sam delete --stack-name vpc-api-dev
```

**Note:** Delete any VPCs created via the API before deleting the stack, or manually delete them from the AWS Console.

## Limitations

- VPCs created are not automatically deleted when the stack is deleted
- No pagination on list endpoint (suitable for small datasets)
- API key must be at least 20 characters
