# Azure Deployment Guide — Project CV-17 Visual Image Search Engine

---

## Azure Services for Visual Image Search

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Vision — Image Retrieval**| Generate image embeddings and find visually similar images                   | Replace your ResNet18 + cosine similarity pipeline |
| **Azure AI Search**                  | Vector search over image embeddings at scale                                 | Replace your in-memory cosine similarity index     |
| **Azure OpenAI Embeddings**          | CLIP-style embeddings for deep visual similarity                             | Replace your ResNet18 feature extractor            |

> **Azure AI Vision Image Retrieval + Azure AI Search** replace your ResNet18 + cosine similarity pipeline with a scalable managed solution.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, cv-service)        | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Blob Storage**        | Store indexed images and search results                                  |
| **Azure AI Search**           | Persistent vector index — replace in-memory similarity store             |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track search latency, similarity scores, request volume              |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Vision Image Retrieval    │
│ CV Service :8001  │    │ + Azure AI Search (vector)         │
│ ResNet18 CNN      │    │ Scalable visual search             │
│ + cosine sim      │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-visual-search --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-visual-search --name visualsearchacr --sku Basic --admin-enabled true
az acr login --name visualsearchacr
ACR=visualsearchacr.azurecr.io
docker build -f docker/Dockerfile.cv-service -t $ACR/cv-service:latest ./cv-service
docker push $ACR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Deploy Container Apps

```bash
az containerapp env create --name visualsearch-env --resource-group rg-visual-search --location uksouth

az containerapp create \
  --name cv-service --resource-group rg-visual-search \
  --environment visualsearch-env --image $ACR/cv-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 1 --memory 2.0Gi

az containerapp create \
  --name backend --resource-group rg-visual-search \
  --environment visualsearch-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars CV_SERVICE_URL=http://cv-service:8001
```

---

## Option B — Use Azure AI Vision + Azure AI Search

```python
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

vision_client = ImageAnalysisClient(
    endpoint=os.getenv("AZURE_VISION_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_VISION_KEY"))
)
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="images",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

def index_image(image_id: str, image_bytes: bytes, metadata: dict) -> dict:
    # Get image description for hybrid search
    result = vision_client.analyze(image_data=image_bytes, visual_features=[VisualFeatures.DENSE_CAPTIONS])
    caption = result.dense_captions.list[0].text if result.dense_captions else ""
    search_client.upload_documents([{"id": image_id, "caption": caption, **metadata}])
    return {"indexed": True, "id": image_id, "caption": caption}

def search_similar(query_image_bytes: bytes, top_k: int = 5) -> list:
    result = vision_client.analyze(image_data=query_image_bytes, visual_features=[VisualFeatures.DENSE_CAPTIONS])
    caption = result.dense_captions.list[0].text if result.dense_captions else ""
    results = search_client.search(search_text=caption, top=top_k)
    return [{"id": r["id"], "score": r["@search.score"], "caption": r.get("caption", "")} for r in results]
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost          |
|--------------------------|-----------|--------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month      |
| Container Apps (cv-svc)  | 1 vCPU    | ~$15–20/month      |
| Container Registry       | Basic     | ~$5/month          |
| Static Web Apps          | Free      | $0                 |
| Azure AI Search          | Basic     | ~$75/month         |
| Azure AI Vision          | S1 tier   | Pay per call       |
| **Total (Option A)**     |           | **~$30–40/month**  |
| **Total (Option B)**     |           | **~$95–115/month** |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-visual-search --yes --no-wait
```
