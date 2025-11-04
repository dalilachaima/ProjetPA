import json
import os
from google import genai
from dotenv import load_dotenv
from django.db import IntegrityError 
from .models import QuizQuestion, Category, Answer 
load_dotenv()
try:
    client = genai.Client()
except Exception as e:
    print(f"Erreur d'initialisation du client Gemini : {e}")
    client = None


#######

def generate_and_save_question(category_name: str, difficulty: int, time_limit: int = 30):
    if client is None:
        print("Le client Gemini n'est pas initialisé.")
        return None
    try:
        category_obj = Category.objects.get(descriptor=category_name)
    except Category.DoesNotExist:
        print(f"Erreur : La catégorie '{category_name}' n'existe pas dans la base de données.")
   
        return None
   
   
   #####
    
    prompt = f"""
    Génère une question de quiz de niveau {difficulty} sur le thème "{category_name}".
    La réponse doit être STRICTEMENT au format JSON : 
    {{ 
        "question": "Votre question ici", 
        "correct_answer": "La bonne réponse", 
        "incorrect_answers": ["Fausses réponse 1", "Fausses réponse 2", "Fausses réponse 3"] 
    }}
    NE RÉPONDEZ QU'AVEC LE CODE JSON.
    """

#######
# 

    print(f"Génération de la question sur '{category_name}' (Difficulté {difficulty})...")
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)

    except (json.JSONDecodeError, Exception) as e:
        print(f"Erreur lors de l'analyse ou de l'appel à l'API : {e}")
        print("Réponse brute de l'IA (pour débogage) :", response.text)
        return None
    
    
    ###

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
    

    