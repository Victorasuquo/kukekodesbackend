# Google Cloud Run Deployment

## Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Docker installed (for local testing)

## Quick Deploy

### 1. Set up Google Cloud
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required services
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Deploy to Cloud Run
```bash
# Deploy directly from source (easiest)
gcloud run deploy kukekodes-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production,DEBUG=false"
```

### 3. Set Environment Variables
```bash
gcloud run services update kukekodes-backend \
  --region us-central1 \
  --set-env-vars "\
DATABASE_URL=postgresql://user:pass@host:5432/db,\
MONGODB_URI=mongodb+srv://...,\
JWT_SECRET=your-secret-key-32-chars-minimum,\
SENDGRID_API_KEY=your-key,\
CLOUDINARY_CLOUD_NAME=your-name,\
CLOUDINARY_API_KEY=your-key,\
CLOUDINARY_API_SECRET=your-secret"
```

## Alternative: Build & Deploy Manually

### Build Docker Image
```bash
# Build locally
docker build -t kukekodes-backend .

# Test locally
docker run -p 8080:8080 --env-file .env kukekodes-backend

# Tag for Google Container Registry
docker tag kukekodes-backend gcr.io/YOUR_PROJECT_ID/kukekodes-backend

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/kukekodes-backend

# Deploy from GCR
gcloud run deploy kukekodes-backend \
  --image gcr.io/YOUR_PROJECT_ID/kukekodes-backend \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Variables

Set these in Cloud Run console or via CLI:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `JWT_SECRET` | ✅ | Min 32 characters |
| `MONGODB_URI` | Optional | MongoDB connection |
| `SENDGRID_API_KEY` | Optional | Email service |
| `CLOUDINARY_*` | Optional | Image uploads |
| `YOUTUBE_API_KEY` | Optional | Video metadata |
| `GEMINI_API_KEY` | Optional | AI features |

## Cloud SQL (Optional)

If using Cloud SQL instead of Supabase:
```bash
# Create instance
gcloud sql instances create kukekodes-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# Connect Cloud Run to Cloud SQL
gcloud run services update kukekodes-backend \
  --add-cloudsql-instances YOUR_PROJECT_ID:us-central1:kukekodes-db
```

## Custom Domain

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service kukekodes-backend \
  --domain api.yourdomain.com \
  --region us-central1
```

## Monitoring

- **Logs**: https://console.cloud.google.com/logs
- **Metrics**: https://console.cloud.google.com/run
- **Errors**: https://console.cloud.google.com/errors

## Costs

Cloud Run pricing:
- First 2 million requests/month: FREE
- CPU: $0.00002400/vCPU-second
- Memory: $0.00000250/GiB-second
- Always-on minimum instances: Extra cost

## Troubleshooting

### Container fails to start
- Check logs: `gcloud run logs read --service kukekodes-backend`
- Verify PORT=8080 is used
- Test locally with Docker first

### Database connection issues
- Whitelist Cloud Run IPs in Supabase
- Use Cloud SQL Auth Proxy for Cloud SQL
- Check connection string format

### Cold start slow
- Set minimum instances: `--min-instances 1`
- Optimize imports and startup code
