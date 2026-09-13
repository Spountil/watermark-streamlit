# Watermark Streamlit App

A production-grade, secure, and automated Streamlit application for batch-watermarking real estate photos. Built for performance, security, and ease of use.

## Features
- **Batch Processing**: Upload multiple high-resolution images simultaneously.
- **HEIC Support**: Natively processes Apple HEIC formats using `pillow-heif`.
- **Memory Optimized**: Uses Streamlit's `session_state` to prevent redundant processing loops.
- **Cloud Storage**: Fetches the official watermark asset directly from Google Cloud Storage.

## Application Workflow

Here is how the Streamlit application processes your images behind the scenes:

```mermaid
flowchart TD
    Start([User uploads HEIC/JPG images]) --> Session[Save images to session state]
    Session --> Adjust[User adjusts watermark scale & opacity]
    Adjust --> Button{Clicks 'Traiter les photos'}
    Button --> Loop[Loop through each image]
    
    Loop --> Convert[Convert HEIC to standard RGB]
    Convert --> Scale[Scale watermark based on slider]
    Scale --> Merge[Overlay watermark with selected opacity]
    Merge --> Zip[Save processed image to Memory ZIP]
    Zip -.-> Loop
    
    Loop --> Done[Generate Download Button]
    Done --> Download([User downloads ZIP file])
    
    classDef action fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000;
    classDef process fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#000;
    
    class Start,Button,Download action;
    class Convert,Scale,Merge,Zip process;
```

## Infrastructure Architecture

The application is deployed on Google Cloud Platform (GCP) with a Zero-Trust security model. The Cloud Run service is completely sealed from the public internet and can only be accessed through the Global Load Balancer and Identity-Aware Proxy (IAP).

```mermaid
graph TD
    User([👤 Authorized User]) -->|HTTPS| GLB[🌐 Global Load Balancer]
    GLB --> IAP{🛡️ Identity-Aware Proxy}
    IAP -->|OAuth 2.0 Check| IAM[Google IAM]
    IAM -.->|Valid Token| IAP
    IAP -->|Internal Traffic| CR[☁️ Cloud Run Container]
    CR -->|Fetch Asset| GCS[(📦 Cloud Storage Bucket)]
    
    classDef secure fill:#e8f4f8,stroke:#2b7fb3,stroke-width:2px;
    classDef compute fill:#f9e8e8,stroke:#c23531,stroke-width:2px;
    
    class IAP,IAM secure;
    class CR compute;
```

## CI/CD Pipeline (GitHub Actions)

Deployments are 100% automated. When code is pushed to the `main` branch, GitHub Actions uses Workload Identity Federation (OIDC) to securely authenticate with Google Cloud without requiring static service account keys.

```mermaid
sequenceDiagram
    participant Dev as 👨‍💻 Developer
    participant GH as 🐙 GitHub Repository
    participant GHA as ⚙️ GitHub Actions
    participant GCP as ☁️ Google Cloud
    
    Dev->>GH: 1. git push origin main
    GH->>GHA: 2. Trigger deploy.yml
    GHA->>GCP: 3. Request short-lived OIDC Token (Workload Identity)
    GCP-->>GHA: 4. Grant access (github-actions-sa)
    GHA->>GCP: 5. Submit source to Cloud Build
    GCP->>GCP: 6. Build Docker Image & Push to Artifact Registry
    GCP->>GCP: 7. Deploy to Cloud Run
    GCP-->>GH: 8. Deployment Successful
```

## Local Development

This project uses [Astral `uv`](https://github.com/astral-sh/uv) for lightning-fast Python dependency management.

### Setup
1. Clone the repository.
2. Ensure you are authenticated with Google Cloud locally so the app can fetch the watermark:
   ```bash
   gcloud auth application-default login
   ```
3. Run the application (`uv` will automatically resolve and install dependencies in milliseconds):
   ```bash
   uv run streamlit run app.py
   ```
