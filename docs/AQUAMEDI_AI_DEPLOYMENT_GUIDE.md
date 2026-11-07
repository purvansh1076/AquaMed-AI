# AQUAMEDI AI — PRODUCTION DEPLOYMENT & DEVOPS GUIDE
**Document Reference**: `AQUA-DEP-GUIDE-2026-V1`  
**Classification**: Infrastructure & Operations Manual  
**Author**: DevOps & Cloud Infrastructure Engineer  

---

## 1. Environment Configurations & Secrets Management

Configuration is loaded using Pydantic Settings from `.env`. A sample configuration template is provided below:

```bash
# Application Environment
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=generate_a_64_char_random_hex_key_here

# Security & JWT Tokens
JWT_SECRET_KEY=generate_another_high_entropy_jwt_signing_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
GUEST_SESSION_EXPIRE_HOURS=24
ENABLE_DEV_DEMO_CREDENTIALS=false

# Production PostgreSQL Database
DATABASE_URL=postgresql+psycopg2://aquamedi_admin:SecurePass2026!@postgres-prod:5432/aquamedi_db

# CORS Origin Whitelist (Comma-separated)
CORS_ORIGINS=https://aquamedi.gov.in,https://expert.aquamedi.gov.in
```

---

## 2. Docker Compose Multi-Container Deployment

To deploy the unified stack locally or on a cloud virtual machine (AWS EC2, Azure VM, GCP Compute Engine):

### Step 1: Clone Repository & Create Environment File
```bash
git clone <repository_url> aquamedi-ai
cd aquamedi-ai
cp backend/.env.example .env
# Edit .env with your production credentials
```

### Step 2: Build and Launch Containers
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
# Ensure all containers (aquamedi_postgres, aquamedi_backend, aquamedi_frontend) report "Up"
```

### Step 4: Run Database Migrations
Migrations run automatically on container startup via `alembic upgrade head`. To manually verify:
```bash
docker compose exec backend alembic current
# Expected: 0002_add_users_table (head)
```

---

## 3. Local Bare-Metal Development Execution

If running directly on a developer workstation without Docker:

### Backend Execution:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Execution:
```powershell
cd frontend
npm install
npm run dev
# Accessible at http://localhost:5173
```

---

## 4. Reverse Proxy & SSL/TLS Configuration (Nginx)

```nginx
server {
    listen 80;
    server_name aquamedi.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aquamedi.gov.in;

    ssl_certificate /etc/letsencrypt/live/aquamedi.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aquamedi.gov.in/privkey.pem;

    # Frontend Static Single Page App
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend FastAPI Gateway
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
