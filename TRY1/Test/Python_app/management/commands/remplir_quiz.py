# Python_app/management/commands/remplir_quiz.py

from django.core.management.base import BaseCommand, CommandError
from Python_app.services import generate_and_save_question
from Python_app.models import Category # Si vous utilisez le modèle Category

class Command(BaseCommand):
    help = 'Génère un nombre spécifié de questions de quiz pour chaque catégorie en utilisant l\'IA.'

    def add_arguments(self, parser):
        # Argument pour spécifier combien de questions générer par catégorie
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Le nombre de questions à générer par catégorie.'
        )
        # Argument pour spécifier le niveau de difficulté par défaut
        parser.add_argument(
            '--difficulty',
            type=int,
            default=3,
            help='Le niveau de difficulté à utiliser (1 à 5).'
        )

    def handle(self, *args, **options):
        # Récupération des arguments
        count = options['count']
        difficulty = options['difficulty']
        
        # Liste des catégories à traiter (ajustez ceci à votre besoin)
        categories_a_traiter = ["Géographie", "Histoire", "Sciences", "Informatique", "Islam", "Culture Generale"] 
        
        # --- Option A: Traiter les catégories existantes dans la BDD ---
        # categories = Category.objects.all()
        # categories_names = [c.name for c in categories]

        # --- Option B: Traiter une liste prédéfinie (celle ci-dessus) ---
        categories_names = categories_a_traiter

        if not categories_names:
            raise CommandError("Aucune catégorie trouvée ou spécifiée pour la génération.")
            
        self.stdout.write(f"Démarrage de la génération : {count} questions, difficulté {difficulty} par catégorie.")

        for category_name in categories_names:
            self.stdout.write(self.style.NOTICE(f'\n-> Génération pour la catégorie: {category_name}...'))
            
            for i in range(count):
                self.stdout.write(f'  - Question {i + 1}/{count}: ', ending='')
                try:
                    # Appel de la fonction de service
                    nouvelle_question = generate_and_save_question(category_name, difficulty)
                    self.stdout.write(self.style.SUCCESS(f'OK. ID: {nouvelle_question.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'ÉCHEC. Erreur: {e}'))
                    # Continue à la prochaine question même en cas d'échec
                    continue
        
        self.stdout.write(self.style.SUCCESS('\nBase de données de questions remplie avec succès! 🎉'))