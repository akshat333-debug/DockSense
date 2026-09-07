# DockSense Web

Operator console for seeded or pipeline-generated incidents.

```bash
python scripts/seed_fake_incidents.py
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
cd apps/web
npm install
npm run dev
```

Set `VITE_API_URL` when the API runs somewhere other than `http://localhost:8000`.
