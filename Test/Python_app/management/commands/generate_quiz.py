from django.core.management.base import BaseCommand, CommandError
import time

try:
    from Python_app.services import generate_and_save_question
except Exception as _e:
    generate_and_save_question = None
    _IMPORT_ERROR_MSG = str(_e)

class Command(BaseCommand):
    help = 'Génère des questions de quiz pour plusieurs catégories et niveaux.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Nombre par catégorie/niveau.')
        parser.add_argument('--use-db', action='store_true', help='Utiliser les catégories présentes en base.')
        parser.add_argument('--categories', type=str, help='Liste de catégories séparées par des virgules (ex: "Histoire,Sciences").')

    def handle(self, *args, **options):
        count = options['count']

        if generate_and_save_question is None or not callable(generate_and_save_question):
            raise CommandError(
                "Impossible d'importer 'generate_and_save_question' depuis Python_app.services.\n"
                "Erreur d'import originale: " + (_IMPORT_ERROR_MSG if '_IMPORT_ERROR_MSG' in globals() else 'unknown')
            )

        # paramètres
        DELAY_ON_FAILURE = 1
        MAX_ATTEMPTS_PER_QUESTION = 5
        difficulty_levels = [1, 2, 3]

        # Détermination des catégories
        categories_to_process = []
        if options.get('categories'):
            categories_to_process = [c.strip() for c in options['categories'].split(',') if c.strip()]
        elif options.get('use_db'):
            try:
                from Python_app.models import Category
                qs = Category.objects.all().values_list('descriptor', flat=True)
                categories_to_process = list(qs)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"[WARN] Impossible de lire les catégories en base: {e}"))
        if not categories_to_process:
            categories_to_process = ["Géographie","Islam", "Histoire", "Sciences", "Informatique", "Culture Générale"]

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Démarrage: {count} questions par niveau ({difficulty_levels}) pour {len(categories_to_process)} catégories."
        ))

        for category_name in categories_to_process:
            self.stdout.write(f'\n--- Catégorie: {category_name} ---')
            for difficulty in difficulty_levels:
                self.stdout.write(self.style.NOTICE(f'  [ Niveau : {difficulty} ]'))
                questions_generated = 0

                while questions_generated < count:
                    self.stdout.write(f'     - Question {questions_generated + 1}/{count}:')
                    success = False

                    for attempt in range(1, MAX_ATTEMPTS_PER_QUESTION + 1):
                        try:
                            new_question = generate_and_save_question(category_name, difficulty)
                            if new_question:
                                self.stdout.write(self.style.SUCCESS(f'       OK — ID: {getattr(new_question, "pk", "N/A")}'))
                                questions_generated += 1
                                success = True
                                break
                            else:
                                if attempt < MAX_ATTEMPTS_PER_QUESTION:
                                    self.stdout.write(self.style.WARNING(f'       ÉCHEC/Doublon — réessai {attempt + 1}/{MAX_ATTEMPTS_PER_QUESTION} après {DELAY_ON_FAILURE}s'))
                                    time.sleep(DELAY_ON_FAILURE)
                                else:
                                    self.stdout.write(self.style.ERROR(f'       ÉCHEC FINAL après {MAX_ATTEMPTS_PER_QUESTION} tentatives — passage à la suivante.'))
                                    # on sort de la boucle d'essais sans incrémenter (évite fausses questions)
                                    break
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'       ERREUR: {e} — passage à la question suivante.'))
                            break

                    if not success:
                        # éviter boucle infinie : incrémenter pour avancer mais loguer
                        questions_generated += 1
                        self.stdout.write(self.style.WARNING('       Avancement forcé (aucune question générée pour ce slot).'))

        self.stdout.write(self.style.SUCCESS('\n✅ Génération terminée.'))