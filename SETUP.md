# StudiServ — Setup Guide

Complete steps to run the project from a fresh clone on any machine.

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Django backend |
| Node.js | 18+ | React frontend (Vite) |
| MariaDB / MySQL | 10.5+ recommended | Database |
| Git | any | Cloning the repo |

## 1. Clone the repo

```bash
git clone https://github.com/Yassine1206/studiserv.git
cd studiserv
```

## 2. Create the database

Open a MySQL/MariaDB shell and run:

```sql
CREATE DATABASE studiserv CHARACTER SET utf8mb4;
CREATE USER 'studiserv_user'@'localhost' IDENTIFIED BY 'Studiserv123!';
GRANT ALL PRIVILEGES ON studiserv.* TO 'studiserv_user'@'localhost';
FLUSH PRIVILEGES;
```

These credentials match `StudiServ/settings.py`. If your DB runs on a different port, edit `DATABASES → PORT` in that file (defaults to `3306`).

## 3. Backend setup

```bash
# Create and activate venv
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install pypdf daphne          # extras used by chatbot/PDF validation/WebSockets

# Apply migrations
python manage.py migrate

# (Recommended) Seed demo data — admin, 3 prestataires, 3 consommateurs,
# services, orders and reviews. Password for all accounts: demo1234
python manage.py seed_demo

# OR create just a superuser
python manage.py createsuperuser

# Start the backend
python manage.py runserver
```

Backend now runs at **http://localhost:8000**.

### MariaDB < 10.5 ?

If you see `You have an error in your SQL syntax... near 'RETURNING'`, your MariaDB is too old for Django 5.2's INSERT...RETURNING. Add this near the top of `StudiServ/settings.py` (before `INSTALLED_APPS`):

```python
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False
```

## 4. Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend now runs at **http://localhost:5173**.

## 5. Use the app

- App: **http://localhost:5173**
- API: **http://localhost:8000**
- Django admin: **http://localhost:8000/admin/**

### Demo accounts (after running `seed_demo`)

Password for all: `demo1234`

| Email | Role |
|---|---|
| `admin@studiserv.tn` | Administrator (can verify cards) |
| `sarra.benali@esprit.tn` | Provider — Design |
| `amine.hammami@enit.tn` | Provider — Web dev |
| `leila.mansouri@isg.tn` | Provider — Tutoring/CV |
| `rayen.khelifi@enit.tn` | Consumer (has placed orders + reviews) |
| `nadia.trabelsi@esprit.tn` | Consumer |
| `youssef.gharbi@isg.tn` | Consumer |

To wipe & recreate demo data:

```bash
python manage.py seed_demo --reset
```

## Demo scenarios

### Provider workflow
1. Sign in as a consumer, browse services, place an order on one.
2. Sign out, sign in as the provider that owns that service.
3. Go to **Commandes** tab → click **Accepter** → status becomes "En cours".
4. Click **Marquer livrée** → status becomes "Terminée".
5. Sign back in as the consumer → leave a review.

### Provider verification workflow
1. Sign up as a new provider — upload a student card.
2. Try to publish a service → blocked: "compte n'est pas encore vérifié".
3. Sign in as `admin@studiserv.tn` → Admin Dashboard → **Vérifications**.
4. Approve or reject the pending card.
5. Sign back in as the provider — publishing now works.

### Chatbot
Open the chatbot bubble (bottom right). Try:
- "Comment passer une commande ?"
- "Comment obtenir le badge de confiance ?"
- "Recommande-moi un prestataire en design"

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | venv not activated. Re-activate it. |
| `Couldn't listen on 127.0.0.1:8000 (WinError 10048)` | Old Django process still running. Find it with `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F`. |
| Chatbot returns "problème de connexion" | Backend not running, or DB error. Check the Django console for tracebacks. |
| Frontend says "Network error" | Backend not running, or CORS issue. Make sure both servers are up. |

## Architecture summary

- **Backend**: Django 5.2 + DRF + Channels (ASGI/Daphne) for WebSockets
- **Frontend**: React 18 + Vite + Axios
- **Database**: MariaDB / MySQL
- **Auth**: JWT (djangorestframework-simplejwt)
- **Chatbot**: Built-in knowledge base + optional ChromaDB + LLM fallback
- **Student card check**: pypdf (PDF) + pytesseract (images), then keyword + matricule heuristic
