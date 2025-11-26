# Génération de questions (Quiz Game)

## 1. Prérequis

- Python installé
- Django installé
- Le projet fonctionne (`python manage.py runserver`)
- Installer la librairie `requests` si vous utilisez une API externe :
  ```
  pip install requests
  ```

## 2. Clé API (optionnel pour IA)

Pour utiliser une IA (OpenAI, Gemini, etc.), ajoutez votre clé dans un fichier `.env` à la racine du projet :

```
GEMINI_API_KEY=VOTRE_CLE_ICI
```

ou

```
OPENAI_API_KEY=VOTRE_CLE_ICI
```

## 3. Ajout des routes et vues

Dans `Python_app/urls.py` ajoutez :

```python
path('generate/', views.generate_questions_view, name='generate_questions'),
path('api/generate/', views.GenerateQuestionsAPIView.as_view(), name='api-generate-questions'),
```

Dans `Python_app/views.py` ajoutez :

```python
def _local_generate_questions(count: int, category: str):
    questions = []
    for i in range(1, count + 1):
        questions.append({
            "question": f"[{category or 'Général'}] Question sample #{i} — Quelle est la réponse ?",
            "choices": ["Réponse A", "Réponse B", "Réponse C", "Réponse D"],
            "answer": "Réponse A"
        })
    return questions

def generate_questions_logic(count: int = 5, category: str = ""):
    return _local_generate_questions(count, category)

def generate_questions_view(request):
    questions = []
    if request.method == "POST":
        try:
            count = int(request.POST.get("count", 5))
        except (ValueError, TypeError):
            count = 5
        category = request.POST.get("category", "").strip()
        questions = generate_questions_logic(count, category)
    return render(request, "generate.html", {"questions": questions})

from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name="dispatch")
class GenerateQuestionsAPIView(View):
    def post(self, request, *args, **kwargs):
        import json
        try:
            payload = json.loads(request.body.decode() or "{}")
        except Exception:
            payload = {}
        count = int(payload.get("count", 5))
        category = payload.get("category", "")
        questions = generate_questions_logic(count, category)
        return JsonResponse({"questions": questions}, safe=False)
```

Créez le template `generate.html` dans `Python_app/templates/` :

```html
<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Générer des questions</title>
  </head>
  <body>
    <h2>Générer des questions (IA)</h2>
    <form method="post">
      {% csrf_token %}
      <label
        >Nombre : <input type="number" name="count" value="5" min="1" max="50"
      /></label>
      <label>
        Thème : <input type="text" name="category" placeholder="ex: histoire"
      /></label>
      <button type="submit">Générer</button>
    </form>
    <hr />
    {% if questions %}
    <h3>Résultats :</h3>
    {% for q in questions %}
    <div>
      <strong>Q{{ forloop.counter }}:</strong> {{ q.question }} {% if q.choices
      %}
      <ul>
        {% for c in q.choices %}
        <li>{{ c }}</li>
        {% endfor %}
      </ul>
      {% endif %} {% if q.answer %}
      <div>Réponse: {{ q.answer }}</div>
      {% endif %}
    </div>
    {% endfor %} {% endif %}
  </body>
</html>
```

## 4. Utilisation

- Relancez le serveur :
  ```
  python manage.py runserver
  ```
- Ouvrez dans le navigateur :
  ```
  http://127.0.0.1:8000/generate/
  ```
- Remplissez le formulaire et cliquez sur "Générer".

## 5. API (optionnel)

Pour générer des questions via l'API :

```bash
curl -X POST -H "Content-Type: application/json" -d '{"count":5,"category":"histoire"}' http://127.0.0.1:8000/api/generate/
```

## 6. Remarques

- Sans clé API, la génération est locale (questions factices).
- Pour utiliser une vraie IA, adaptez la fonction `generate_questions_logic` pour appeler l'API de votre choix.
