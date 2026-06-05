# Backend API - TraceOps

## Servicio requerido

FastAPI debe desplegarse como servicio Python/Docker, no en Netlify.

Opciones recomendadas para prueba cliente:

- Render Web Service con Dockerfile.
- Railway/Fly.io.
- DigitalOcean App Platform.
- VPS Hetzner/DigitalOcean con Docker Compose.

## Comando de arranque

`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Si el proveedor no inyecta `$PORT`, usar `8000`.

## Variables principales

- `TRACEOPS_ENV=production`
- `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres`
- `REDIS_URL=redis://...`
- `STORAGE_PROVIDER=supabase`
- `SUPABASE_STORAGE_ENDPOINT=PROJECT_REF.storage.supabase.co/storage/v1/s3`
- `SUPABASE_STORAGE_PUBLIC_ENDPOINT=PROJECT_REF.storage.supabase.co/storage/v1/s3`
- `SUPABASE_STORAGE_BUCKET=traceops-evidences`
- `SUPABASE_STORAGE_ACCESS_KEY_ID=...`
- `SUPABASE_STORAGE_SECRET_ACCESS_KEY=...`
- `SUPABASE_STORAGE_REGION=us-east-1`
- `SUPABASE_STORAGE_SECURE=true`
- `JWT_SECRET_KEY=GENERAR_SECRET_LARGO`
- `BOOTSTRAP_ENABLED=false`
- `CORS_ORIGINS=https://URL_NETLIFY`

## Supabase Storage

Para la demo, crear el bucket `traceops-evidences` en Supabase Storage antes de cargar fotos. La API usara el protocolo S3 de Supabase para generar URLs presignadas de subida, descarga y borrado.

## Salud

Endpoint:

`GET /health`

Docs API:

`GET /docs`
