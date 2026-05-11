# Projet Django - Gestion des services

Ce projet Django genere les entites du diagramme UML fourni et des templates CRUD simples pour les gerer.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Puis ouvrir:

- Application: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Entites incluses

- Compte
- Utilisateur
- Consommateur
- Prestataire
- Profil
- Competence
- Service
- Demande
- Discussion
- Recommendation

