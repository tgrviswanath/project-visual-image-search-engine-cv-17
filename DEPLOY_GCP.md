# GCP Deployment Guide — Project CV-17 Visual Image Search Engine

---

## GCP Services for Visual Image Search

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Vertex AI Matching Engine**        | Vector similarity search over image embeddings at scale                      | Replace your in-memory cosine similarity index     |
| **Vertex AI Multimodal Embeddings**  | multimodalembedding@001 for generating deep image embeddings                 | Replace your ResNet18 feature extractor            |
| **Cloud Vision API — Web Detection** | Find visually similar images on the web                                      | When you need web-scale image search               |

> **Vertex AI Multimodal Embeddings + Matching Engine** replace your ResNet18 + cosine similarity pipeline with a scalable managed solution.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + cv-service containers — serverless, scales to zero    | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Cloud Storage**              | Store indexed images and search results                                   |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track search latency, similarity scores, request volume                   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Vertex AI Multimodal Embeddings    │
│ CV Service :8001  │    │ + Vertex AI Matching Engine        │
│ ResNet18 CNN      │    │ Scalable visual search             │
│ + cosine sim      │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create visualsearch-cv-project --name="Visual Image Search"
gcloud config set project visualsearch-cv-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com vision.googleapis.com \
  storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create visualsearch-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/visualsearch-cv-project/visualsearch-repo
docker build -f docker/Dockerfile.cv-service -t $AR/cv-service:latest ./cv-service
docker push $AR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Deploy to Cloud Run

```bash
gcloud run deploy cv-service \
  --image $AR/cv-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 2Gi --cpu 1

CV_URL=$(gcloud run services describe cv-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars CV_SERVICE_URL=$CV_URL
```

---

## Option B — Use Vertex AI Multimodal Embeddings + Matching Engine

```python
import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel, Image
from google.cloud import aiplatform

vertexai.init(project="visualsearch-cv-project", location="europe-west2")
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

def embed_image(image_bytes: bytes) -> list:
    image = Image(image_bytes=image_bytes)
    embeddings = model.get_embeddings(image=image)
    return embeddings.image_embedding

def index_image(image_id: str, image_bytes: bytes) -> dict:
    embedding = embed_image(image_bytes)
    # Store in Matching Engine index (pre-created)
    return {"indexed": True, "id": image_id, "embedding_dim": len(embedding)}

def search_similar(query_bytes: bytes, index_endpoint_name: str, top_k: int = 5) -> list:
    query_embedding = embed_image(query_bytes)
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name)
    response = index_endpoint.find_neighbors(
        deployed_index_id="visualsearch_index",
        queries=[query_embedding],
        num_neighbors=top_k
    )
    return [{"id": n.id, "distance": n.distance} for n in response[0]]
```

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (cv-service)     | 1 vCPU / 2 GB         | ~$12–18/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Vertex AI Matching Engine  | Pay per node hour     | ~$65–100/month     |
| **Total (Option A)**       |                       | **~$23–35/month**  |
| **Total (Option B)**       |                       | **~$78–120/month** |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete cv-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete visualsearch-repo --location=$GCP_REGION --quiet
gcloud projects delete visualsearch-cv-project
```
