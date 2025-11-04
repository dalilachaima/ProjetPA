import json
import os
from google import genai
from dotenv import load_dotenv
from django.db import IntegrityError 
from .models import QuizQuestion, Category, Answer 

load_dotenv()

# --- Section d'Initialisation Corrigée ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None 

if GEMINI_API_KEY:
    try:
        # Configuration globale de l'API
        client = genai.Client(api_key=GEMINI_API_KEY)
        # Création de l'objet modèle pour les requêtes futures
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        print("Client Gemini initialisé avec succès (Modèle gemini-2.5-flash chargé).")
    except Exception as e:
        print(f"Erreur de configuration de l'API Gemini : {e}")
else:
    print("Erreur : La variable d'environnement GEMINI_API_KEY n'est pas définie.")

# ------------------------------------------

def generate_and_save_question(category: str, difficulty: int, time_limit: int = 30):
    # Utiliser la nouvelle variable de modèle
    if gemini_model is None:
        print("Le client Gemini n'est pas initialisé.")
        return None
        
    try:
        # Assurez-vous que l'API de génération a le même nom de modèle si vous voulez le changer
        # gemini_model = genai.GenerativeModel('gemini-2.0-flash') 
        category_obj = Category.objects.get(descriptor=category)
    except Category.DoesNotExist:
        print(f"Erreur : La catégorie '{category}' n'existe pas dans la base de données.")
        return None
    
    # ... (Le reste du prompt est correct)
    prompt = f"""
    Génère une question de quiz de niveau {difficulty} sur le thème "{category}".
    La réponse doit être STRICTEMENT au format JSON : 
    {{ 
        "question": "Votre question ici", 
        "correct_answer": "La bonne réponse", 
        "incorrect_answers": ["Fausses réponse 1", "Fausses réponse 2", "Fausses réponse 3"] 
    }}
    NE RÉPONDEZ QU'AVEC LE CODE JSON.
    """

    print(f"Génération de la question sur '{category}' (Difficulté {difficulty})...")
    
    try:
        # --- Appel à l'API Corrigé ---
        response = gemini_model.generate_content(contents=prompt)
        # -----------------------------
        
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)

    except (json.JSONDecodeError, Exception) as e:
        print(f"Erreur lors de l'analyse ou de l'appel à l'API : {e}")
        # La réponse brute peut parfois être trop longue ou inexistante,
        # vérifiez si 'response' est défini avant d'y accéder.
        if 'response' in locals() and hasattr(response, 'text'):
            print("Réponse brute de l'IA (pour débogage) :", response.text)
        return None
    
    
    ### (La sauvegarde en base de données est correcte)
    try:
        new_question = QuizQuestion.objects.create(
            text=data['question'],
            Category=category_obj,
            Difficulty=difficulty,
            TimeLimit=time_limit
        )
        print(f"Question (ID: {new_question.pk}) créée : {new_question.text[:40]}...")

        Answer.objects.create(
            text=data['correct_answer'],
            Question=new_question,
            IsCorrect=True
        )
        
        for incorrect_text in data['incorrect_answers']:
            Answer.objects.create(
                text=incorrect_text,
                Question=new_question,
                IsCorrect=False
            )
            
        print("Réponses enregistrées avec succès.")
        return new_question
        
    except IntegrityError as e:
        print(f"Erreur d'intégrité de la base de données lors de la sauvegarde : {e}")
        return None