# Instructions rapides pour exécuter le projet Django (Windows) :
# - Ouvrir le terminal à la racine du projet, p.ex.:
#     cd "c:\Users\HP\Desktop\newprjpa - Copy"
# - Créer/activer un venv:
#     python -m venv venv
#     .\venv\Scripts\Activate
# - Installer dépendances:
#     pip install -r requirements.txt   (ou pip install django)
# - Appliquer migrations:
#     python manage.py migrate
# - Lancer serveur:
#     python manage.py runserver
# - Accéder à l'app: http://127.0.0.1:8000/

from django.apps import AppConfig


class PythonAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Python_app'