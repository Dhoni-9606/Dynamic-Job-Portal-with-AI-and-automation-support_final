# Production deployment

## Render backend

The root `render.yaml` defines the Django web service and its PostgreSQL database. In Render, create a Blueprint from this repository and deploy it. The Blueprint installs `requirements.txt`, collects static files, applies migrations before each deploy, and starts Gunicorn. Its health check uses `/health/`.

The Blueprint generates `SECRET_KEY` and connects `DATABASE_URL` to the provisioned Render PostgreSQL database. It configures the Render API hostname and the Vercel frontend origin for allowed hosts, CORS, and CSRF. Email delivery is optional; set `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` in the Render service environment to enable SMTP.

Uploaded media currently uses the service filesystem. Render service filesystems are ephemeral, so configure external object storage before relying on persistent resume or profile image uploads.

## Vercel frontend

Set the Vercel project root to `frontend`, framework preset to Vite, build command to `npm run build`, and output directory to `dist`. Set this environment variable for Production and redeploy:

```text
VITE_API_BASE_URL=https://dynamic-job-portal-with-ai-and.onrender.com/api
```

The included `frontend/vercel.json` routes frontend paths to the Vite application so browser refreshes on client-side routes work.
