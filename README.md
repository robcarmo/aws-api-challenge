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
- AWS SAM CLI installed (`brew install aws-sam-cli` on macOS)
- Python 3.11+

## Deployment

```bash
cd aws-api-challenge

# Build the application
sam build

# Deploy (first time - guided)
sam deploy --guided --capabilities CAPABILITY_NAMED_IAM
```

During guided deployment, you'll be prompted for:
- **Stack Name**: e.g., `vpc-management-api`
- **AWS Region**: e.g., `us-east-1`
- **Environment**: `dev`, `staging`, or `prod`
- **ApiKeyValue**: Your API key (**minimum 20 characters**, e.g., `my-secure-api-key-12345678`)

For subsequent deployments:
```bash
sam deploy --parameter-overrides "Environment=dev ApiKeyValue=my-secure-api-key-12345678" --capabilities CAPABILITY_NAMED_IAM
```

After deployment, note the outputs:
- **ApiEndpoint**: Your API URL (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/dev`)
- **ApiKeyId**: The API Key ID for reference

## Authentication

All endpoints except `/health` require API Key authentication.

Include the API key in requests via the `x-api-key` header:
```bash
-H "x-api-key: my-secure-api-key-12345678"
```

## API Endpoints

Replace `{api-endpoint}` with your deployed API URL (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/dev`).

### Health Check (No Auth Required)
```bash
curl https://{api-endpoint}/health
```

**Response:**
```json
{"status": "healthy", "timestamp": "2025-12-14T15:59:12.779117"}
```

### Create VPC
```bash
curl -X POST https://{api-endpoint}/vpcs \
  -H "x-api-key: my-secure-api-key-12345678" \
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
  "created_at": "2025-12-14T15:59:41.595909"
}
```

### List VPCs
```bash
curl https://{api-endpoint}/vpcs \
  -H "x-api-key: my-secure-api-key-12345678"
```

**Response:**
```json
{
  "vpcs": [...],
  "count": 1
}
```

### Get VPC Details
```bash
curl https://{api-endpoint}/vpcs/{vpc_id} \
  -H "x-api-key: my-secure-api-key-12345678"

# Include live AWS data
curl "https://{api-endpoint}/vpcs/{vpc_id}?include_live=true" \
  -H "x-api-key: my-secure-api-key-12345678"
```

### Delete VPC
```bash
curl -X DELETE https://{api-endpoint}/vpcs/{vpc_id} \
  -H "x-api-key: my-secure-api-key-12345678"
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
aws-api-challenge/
├── src/
│   ├── app/
│   │   ├── handlers/          # Lambda handlers
│   │   │   └── vpc_handler.py
│   │   ├── services/          # Business logic
│   │   │   ├── vpc_service.py
│   │   │   └── dynamodb_service.py
│   │   └── models/            # Data models
│   │       └── vpc.py
│   └── requirements.txt       # Lambda dependencies
├── tests/
│   └── unit/
│       └── test_vpc_handler.py
├── template.yaml              # SAM template
├── requirements.txt           # Dev dependencies
└── README.md
```

## Cleanup

1. First, delete any VPCs created via the API:
```bash
curl -X DELETE https://{api-endpoint}/vpcs/{vpc_id} \
  -H "x-api-key: my-secure-api-key-12345678"
```

2. Then delete the CloudFormation stack:
```bash
sam delete --stack-name {your-stack-name}
```

## Notes

- API key must be at least 20 characters
- VPCs created via the API are real AWS resources and will incur costs if not deleted
- The `--capabilities CAPABILITY_NAMED_IAM` flag is required for deployment
