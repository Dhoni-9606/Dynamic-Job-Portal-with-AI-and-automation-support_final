# Production deployment

## Render backend

The root `render.yaml` defines the Django web service and its PostgreSQL database. In Render, create or sync a Blueprint from this repository and deploy it. The backend service root is `backend`, so dependency installation uses `backend/requirements.txt`; it collects static files, applies migrations before each deploy, and starts Gunicorn from the Django project directory. Its health check uses `/health/`.

If you keep a manually created Render service instead of syncing the Blueprint, set its Root Directory to `backend`, Build Command to `./build.sh`, Pre-Deploy Command to `python manage.py migrate --noinput`, Start Command to `gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile - --timeout 120`, and Health Check Path to `/health/`. Ensure that service has `DEBUG=False`, a generated `SECRET_KEY`, and a Render PostgreSQL `DATABASE_URL`.

The Blueprint generates `SECRET_KEY` and connects `DATABASE_URL` to the provisioned Render PostgreSQL database. It configures the Render API hostname and the Vercel frontend origin for allowed hosts, CORS, and CSRF. Email delivery is optional; set `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` in the Render service environment to enable SMTP.

Uploaded media currently uses the service filesystem. Render service filesystems are ephemeral, so configure external object storage before relying on persistent resume or profile image uploads.

## Vercel frontend

Set the Vercel project root to `frontend`, framework preset to Vite, build command to `npm run build`, and output directory to `dist`. Set this environment variable for Production and redeploy:

```text
VITE_API_BASE_URL=https://dynamic-job-portal-with-ai-and.onrender.com/api
```

The included `frontend/vercel.json` routes frontend paths to the Vite application so browser refreshes on client-side routes work.
