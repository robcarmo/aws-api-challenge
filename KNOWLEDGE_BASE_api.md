# Knowledge Base: AWS VPC Management API

This document serves as a knowledge base for the `aws-api-challenge` repository. It outlines the project structure, naming conventions, coding standards, and architectural decisions to assist in understanding and maintaining the codebase.

## 1. Project Overview

**Description:**
A serverless API built with AWS SAM (Serverless Application Model) for creating and managing AWS VPCs and Subnets. It uses a dual-store approach where metadata is stored in DynamoDB while actual resources are provisioned in AWS EC2.

**Core Technologies:**
- **Language:** Python 3.11
- **Framework:** AWS SAM
- **Infrastructure:** AWS CloudFormation (via SAM)
- **AWS Services:** Lambda, API Gateway, DynamoDB, EC2, IAM
- **Libraries:** `boto3`, `pydantic` (implied or similar via dataclasses), `pytest`

## 2. Project Structure

The project follows a layered architecture to separate concerns:

```
aws-api-challenge/
├── src/
│   └── app/
│       ├── handlers/          # Entry points for Lambda functions
│       │   └── vpc_handler.py # Handles HTTP events, request parsing, response formatting
│       ├── services/          # Business logic and external service integration
│       │   ├── vpc_service.py # AWS EC2 interactions (Create/Delete VPCs/Subnets)
│       │   └── dynamodb_service.py # Database interactions (Metadata storage)
│       └── models/            # Data transfer objects and domain entities
│           └── vpc.py         # Dataclasses for VPC and Subnet definitions
├── template.yaml              # AWS SAM Infrastructure-as-Code definition
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## 3. Naming Conventions

### 3.1 Code (Python)
- **Variables & Functions:** `snake_case` (e.g., `create_vpc`, `vpc_id`)
- **Classes:** `CamelCase` (e.g., `VpcService`, `DynamoDBService`)
- **Constants:** `UPPER_CASE` (e.g., `LOG_LEVEL` in environment variables)
- **Files:** `snake_case.py` (e.g., `vpc_handler.py`)

### 3.2 Infrastructure (AWS/SAM)
- **Logical IDs:** `CamelCase` (e.g., `VpcApi`, `VpcTable`, `CreateVpcFunction`)
- **Resource Names (Physical IDs):** Kebab-case pattern often including environment (e.g., `vpc-api-create-dev`, `vpc-api-resources-dev`)
- **DynamoDB Keys:**
  - **Partition Key (PK):** `pk` (String)
  - **Sort Key (SK):** `sk` (String)
  - **Value Pattern:** `VPC#{vpc_id}` for PK, `METADATA` for SK.

### 3.3 API
- **URL Paths:** Kebab-case, plural nouns (e.g., `/vpcs`, `/health`)
- **Query Parameters:** `snake_case` (e.g., `include_live`)
- **JSON Fields:** `snake_case` (e.g., `cidr_block`, `vpc_id`)

## 4. Coding Standards

### 4.1 Type Safety
- **Type Hinting:** Extensive use of Python `typing` module (`List`, `Dict`, `Any`, `Optional`).
- **Data Models:** Use of `@dataclass` for structural validation and definition (e.g., `CreateVpcRequest`, `SubnetDefinition`).
- **Enums:** Use of `Enum` for fixed sets of values (e.g., `SubnetType`).

### 4.2 Error Handling
- **Pattern:** `try/except` blocks in Handler layer.
- **Response:** Standardized error response format via `_response` helper.
- **HTTP Codes:**
  - `200`: Success
  - `201`: Created
  - `400`: Bad Request (Validation error, JSON error)
  - `404`: Not Found
  - `500`: Internal Server Error

### 4.3 Logging
- **Library:** Standard Python `logging`.
- **Level:** Configurable via `LOG_LEVEL` env var.
- **Content:** Logs errors with `exc_info=True` for stack traces.

### 4.4 Configuration
- **Environment Variables:** Used for dynamic configuration (Table names, Log levels).
- **Injection:** Passed to Lambda functions via `template.yaml`.

## 5. Architectural Decisions

### 5.1 Serverless Compute
- **Decision:** Use AWS Lambda for compute.
- **Rationale:** Cost-effective for sporadic API usage, scales automatically, minimal operational overhead.

### 5.2 Dual-State Management
- **Decision:** Maintain VPC metadata in DynamoDB separate from actual AWS resource state.
- **Rationale:** Allows for application-specific metadata (project, environment tags) to be queried quickly without making slow AWS API calls. "Live" data fetching is optional via query param.

### 5.3 Synchronous Provisioning
- **Decision:** The `create_vpc` operation waits for resources to be available (`waiter` usage).
- **Implication:** API calls might be slower (timeout considerations), but ensures resources are ready when the client receives a 201 response.

### 5.4 Single Table Design (DynamoDB)
- **Decision:** Generic `pk` and `sk` attribute names.
- **Rationale:** Flexible schema allowing future entities (e.g., Subnets as separate items) without schema migration. Current usage: `pk=VPC#{id}`, `sk=METADATA`.

### 5.5 Security
- **Authentication:** API Gateway API Keys required for all non-health endpoints.
- **IAM Roles:** Least privilege principle. Separate policies for DynamoDB access and EC2 VPC access.

### 5.6 Environment Isolation
- **Pattern:** `Environment` parameter in CloudFormation.
- **Outcome:** Deploys separate stacks for `dev`, `staging`, `prod` with suffixed resource names to avoid collisions.
