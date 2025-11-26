import os
import django
from django.db.models import Count 

# --- 1. Configuration de l'environnement Django ---
# IMPORTANT : Assurez-vous que 'Test.settings' est le nom correct de votre fichier de paramètres.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Test.settings') 
try:
    django.setup()
except Exception as e:
    print(f"Erreur de configuration Django : {e}")
    print("Vérifiez si 'Test.settings' est le chemin correct et si l'environnement est activé.")
    exit()

# --- 2. Importations des Modèles et Services ---
from Python_app.models import Category
from Python_app.services import generate_and_save_question 

# --- 3. Paramètres de Génération ---
DIFFICULTIES = [1, 2, 3] # Niveaux de difficulté à remplir
QUESTIONS_PER_DIFFICULTY = 5 # Nombre cible de questions par niveau/catégorie

print("--- Début du Peuplement de la Base de Données Quiz ---")

# --- 4. Logique de Génération ---
try:
    categories = Category.objects.all()

    if not categories:
        print("ATTENTION : Aucune catégorie trouvée. Veuillez en créer dans l'interface /admin/.")
    else:
        for category in categories:
            print(f"\n[Catégorie : {category.descriptor}]")
            
            for difficulty in DIFFICULTIES:
                
                # Correction de la relation inverse : 'category.questions'
                existing_count = category.questions.filter(Difficulty=difficulty).count()
                
                needed_count = QUESTIONS_PER_DIFFICULTY - existing_count
                
                if needed_count > 0:
                    print(f"  -> Niveau {difficulty}: Génération de {needed_count} question(s)...")
                    
                    for i in range(needed_count):
                        print(f"    Génération n°{i+1}/{needed_count}...")
                        
                        # Correction du nom d'argument : 'difficulty'
                        new_question = generate_and_save_question(
                            category_name=category.descriptor, 
                            difficulty=difficulty # Nom d'argument corrigé
                        )
                        
                        if new_question:
                            print(f"      ✅ Question ajoutée (ID: {new_question.pk}).")
                        else:
                            print("      ❌ ÉCHEC de la génération (Quota API atteint ou problème réseau).")
                else:
                    print(f"  -> Niveau {difficulty}: {existing_count} questions déjà présentes. Saut de la génération.")
                    
except Exception as e:
    print(f"\nUne erreur inattendue est survenue lors de l'exécution du script : {e}")
    
print("\n--- Peuplement terminé. ---")