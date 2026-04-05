# AWS Deployment Guide — Project CV-17 Visual Image Search Engine

---

## AWS Services for Visual Image Search

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Rekognition**     | Web detection — find visually similar images on the web                      | When you need web-scale image search               |
| **Amazon OpenSearch**      | k-NN vector search over ResNet18 embeddings at scale                         | Replace your in-memory cosine similarity index     |
| **Amazon Bedrock**         | Titan Multimodal Embeddings for generating deep image embeddings             | Replace your ResNet18 feature extractor            |

> **Amazon Bedrock Titan Multimodal Embeddings + Amazon OpenSearch k-NN** replace your ResNet18 + cosine similarity pipeline with a scalable managed solution.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + cv-service containers in a private VPC                | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon S3**            | Store indexed images and search results                                   |
| **Amazon OpenSearch**    | Persistent vector index — replace in-memory similarity store              |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track search latency, similarity scores, request volume                   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Bedrock Titan Embeddings           │
│ CV Service :8001  │    │ + OpenSearch k-NN                  │
│ ResNet18 CNN      │    │ Scalable visual search             │
│ + cosine sim      │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name visualsearch/cv-service --region $AWS_REGION
aws ecr create-repository --repository-name visualsearch/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.cv-service -t $ECR/visualsearch/cv-service:latest ./cv-service
docker push $ECR/visualsearch/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/visualsearch/backend:latest ./backend
docker push $ECR/visualsearch/backend:latest
```

---

## Step 2 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name visualsearch-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/visualsearch/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "CV_SERVICE_URL": "http://cv-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "1 vCPU", "Memory": "2 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Bedrock Titan Embeddings + OpenSearch

```python
import boto3, json, base64
from opensearchpy import OpenSearch, RequestsHttpConnection

bedrock = boto3.client("bedrock-runtime", region_name="eu-west-2")
os_client = OpenSearch(hosts=[{"host": "<opensearch-endpoint>", "port": 443}], use_ssl=True, http_compress=True)

def embed_image(image_bytes: bytes) -> list:
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-image-v1",
        body=json.dumps({"inputImage": base64.b64encode(image_bytes).decode()}),
        contentType="application/json"
    )
    return json.loads(response["body"].read())["embedding"]

def index_image(image_id: str, image_bytes: bytes, metadata: dict) -> dict:
    embedding = embed_image(image_bytes)
    os_client.index(index="images", id=image_id, body={"embedding": embedding, **metadata})
    return {"indexed": True, "id": image_id}

def search_similar(query_bytes: bytes, top_k: int = 5) -> list:
    query_embedding = embed_image(query_bytes)
    response = os_client.search(
        index="images",
        body={"query": {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}}}
    )
    return [{"id": h["_id"], "score": h["_score"], **h["_source"]} for h in response["hits"]["hits"]]
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 1 vCPU / 2 GB     | ~$20–25/month      |
| App Runner (cv-service)    | 1 vCPU / 2 GB     | ~$20–25/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Amazon OpenSearch          | t3.small.search   | ~$25–35/month      |
| Bedrock Titan Embeddings   | Pay per token     | ~$1–3/month        |
| **Total (Option A)**       |                   | **~$43–57/month**  |
| **Total (Option B)**       |                   | **~$49–70/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name visualsearch/backend --force
aws ecr delete-repository --repository-name visualsearch/cv-service --force
```
