from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
from .models import Category, QuizQuestion, Answer, PlayerScore, PlayerAnswer, GameSession
from .services import generate_and_save_question # Assurez-vous que cette fonction existe
import random

# DRF imports (Avec gestion des exceptions si DRF n'est pas installé)
try:
    from rest_framework import status, viewsets, permissions
    from rest_framework.views import APIView
    from rest_framework.response import Response
except Exception:
    status = type('status', (), {'HTTP_200_OK': 200, 'HTTP_201_CREATED': 201, 'HTTP_400_BAD_REQUEST': 400, 'HTTP_401_UNAUTHORIZED': 401})()
    APIView = object
    Response = dict
    viewsets = type('viewsets', (), {'ModelViewSet': object})()
    permissions = type('permissions', (), {'AllowAny': object, 'IsAuthenticated': object})()

from .serializers import (
    PlayerScoreSerializer, PlayerAnswerSerializer, QuizQuestionSerializer,
    GameSessionSerializer, UserSerializer, UserRegistrationSerializer,
    LoginSerializer
)

# =================================================================
# ===== I. VUES WEB (Rendu HTML) =====
# =================================================================

def home_view(request):
    """Page d'atterrissage avec connexion/inscription."""
    if request.user.is_authenticated:
        return redirect('main_menu')
    return render(request, 'landing.html')

@login_required(login_url='/')
def main_menu_view(request):
    """Affiche le menu principal de sélection des jeux."""
    context = {'user': request.user}
    return render(request, 'main_menu.html', context)



@login_required
def offline_category_selection(request):
    """Affiche la liste des catégories pour le jeu offline."""
    default_categories = ["Géographie", "Histoire", "Sciences", "Informatique", "Islam", "Culture Générale"]
    try:
        # Assure l'existence des catégories par défaut
        if not Category.objects.exists():
            for name in default_categories:
                Category.objects.get_or_create(descriptor=name)
    except Exception:
        pass
    categories = Category.objects.all()
    return render(request, 'offline/category_selection.html', {'categories': categories, 'page_title': "Choisir une Catégorie"})



@login_required
def offline_game_view(request, category_id):
    """Affiche une question de quiz et gère la soumission de réponse (mode hors ligne). Pré-génère les questions au début."""
    category = get_object_or_404(Category, pk=category_id)
    
    game_key = f'offline_game_{category_id}'
    game_data = request.session.get(game_key)
    
    if not game_data:
        # Pré-générer les questions
        questions = []
        num_questions = 10  # Nombre de questions à pré-générer
        for _ in range(num_questions):
            question = generate_and_save_question(category.descriptor, difficulty=2)
            if question:
                questions.append({
                    'id': question.pk,
                    'text': question.text,
                    'answers': list(question.answers.values('pk', 'text', 'IsCorrect'))
                })
        if not questions:
            return render(request, 'error.html', {'message': "Impossible de générer des questions."})
        
        game_data = {
            'questions': questions,
            'current_question': 0,
            'score': 0,
        }
        request.session[game_key] = game_data
    
    current_question = game_data['current_question']
    if current_question >= len(game_data['questions']):
        # Fin du jeu
        score = game_data['score']
        total = len(game_data['questions'])
        del request.session[game_key]
        return render(request, 'offline/game.html', {
            'category': category,
            'end_game': True,
            'score': score,
            'total': total,
            'page_title': f"Fin du Quiz : {category.descriptor}"
        })
    
    question_data = game_data['questions'][current_question]
    question = QuizQuestion.objects.get(pk=question_data['id'])
    answers = [Answer.objects.get(pk=a['pk']) for a in question_data['answers']]
    random.shuffle(answers)
    
    context = {
        'category': category, 'question': question, 'answers': answers,
        'page_title': f"Quiz : {category.descriptor}",
        'submitted': False,
    }

    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer_id')
        if selected_answer_id:
            selected_answer = Answer.objects.get(pk=selected_answer_id)
            is_correct = selected_answer.IsCorrect
            correct_answer = Answer.objects.get(Question=question, IsCorrect=True)
            if is_correct:
                game_data['score'] += 1
            game_data['current_question'] += 1
            request.session[game_key] = game_data
            context.update({
                'submitted': True,
                'is_correct': is_correct,
                'submitted_answer_id': int(selected_answer_id),
                'correct_answer_id': correct_answer.pk,
            })
        else:
            context['error'] = "No answer selected"

    return render(request, 'offline/game.html', context)



@login_required
def multiplayer_initial_setup(request):
    """Affiche le formulaire initial pour saisir le nombre de joueurs ET le nombre de questions."""
    MAX_PLAYERS = 6
    MIN_QUESTIONS = 4
    MAX_QUESTIONS = 20

    if request.method == 'POST':
        try:
            num_players = int(request.POST.get('num_players', 2))
            num_questions = int(request.POST.get('num_questions', 10))
            
            if not (2 <= num_players <= MAX_PLAYERS):
                messages.error(request, f"Le nombre de joueurs doit être compris entre 2 et {MAX_PLAYERS}.")
            elif not (MIN_QUESTIONS <= num_questions <= MAX_QUESTIONS):
                messages.error(request, f"Le nombre de questions doit être compris entre {MIN_QUESTIONS} et {MAX_QUESTIONS}.")
            elif num_questions % 2 != 0:
                messages.error(request, "Le nombre de questions doit être pair pour l'équité.")
            else:
                request.session['num_players_to_register'] = num_players
                request.session['num_questions'] = num_questions
                return redirect('multiplayer_lobby')
        except ValueError:
            messages.error(request, "Veuillez saisir des nombres valides.")
            
    context = {
        'page_title': "Configuration de la Partie Multijoueur",
        'max_players': MAX_PLAYERS,
        'min_questions': MIN_QUESTIONS,
        'max_questions': MAX_QUESTIONS,
    }
    return render(request, 'multiplayer/initial_setup.html', context)


@login_required 
def multiplayer_lobby_view(request):
    """Affiche le formulaire pour saisir les noms des joueurs ET choisir la catégorie."""
    num_players = request.session.get('num_players_to_register') 
    num_questions = request.session.get('num_questions')
    
    if not num_players or not num_questions:
        messages.warning(request, "Veuillez d'abord configurer la partie.")
        return redirect('multiplayer_initial_setup')
        
    categories = Category.objects.all()
    if not categories.exists():
        messages.error(request, "Veuillez créer des catégories avant de démarrer une partie multijoueur.")
        return redirect('main_menu')
        
    AVAILABLE_COLORS = ['#FF6347', '#4682B4', '#3CB371', '#FFA500', '#9370DB', '#F08080'] 
    
    if request.method == 'POST':
        selected_category_id = request.POST.get('category_id') 
        is_random = request.POST.get('is_random') == 'on'
        
        if not selected_category_id and not is_random:
            messages.error(request, "Veuillez sélectionner une catégorie ou choisir le mode Aléatoire.")
            context = {'page_title': "Lobby Multijoueur", 'player_range': range(1, num_players + 1), 'num_players': num_players, 'categories': categories, 'num_questions': num_questions}
            return render(request, 'multiplayer/lobby.html', context)


        player_names = {}
        for i in range(1, num_players + 1): 
            name = request.POST.get(f'player_name_{i}', f'Joueur {i}').strip()
            if name:
                 player_names[i] = name

        # Initialisation de la session de jeu
        random.shuffle(AVAILABLE_COLORS)
        
        players = []
        for i, (index, name) in enumerate(player_names.items()):
            players.append({
                'id': index,
                'name': name,
                'color': AVAILABLE_COLORS[i % len(AVAILABLE_COLORS)],
                'score': 0,
            })
            
        request.session['multiplayer_game'] = {
            'players': players,
            'current_turn_index': 0,
            'category_id': int(selected_category_id) if selected_category_id else None,
            'is_random': is_random,
            'num_questions': num_questions,
            'current_question': 0,
            'game_session_id': None,  # Will be set when game starts
        }
        
        del request.session['num_players_to_register']
        del request.session['num_questions']
        
        messages.success(request, "Lobby créé ! Début du jeu.")
        return redirect('multiplayer_game_start') 
        
    # Affichage du formulaire
    player_range = range(1, num_players + 1)
    
    context = {
        'page_title': "Lobby Multijoueur",
        'player_range': player_range,
        'num_players': num_players,
        'categories': categories,
        'num_questions': num_questions,
    }
    return render(request, 'multiplayer/lobby.html', context)


@login_required
def multiplayer_game_start(request):
    """
    Affiche la question actuelle, gère le tour du joueur, le score et le passage au joueur suivant.
    Logique tour par tour: Question 1 pour Joueur 1, Question 2 pour Joueur 2, etc.
    Pré-génère toutes les questions au début pour éviter les répétitions.
    """
    game_data = request.session.get('multiplayer_game')

    if not game_data:
        messages.error(request, "Aucune partie multijoueur en cours. Veuillez créer un lobby.")
        return redirect('multiplayer_initial_setup')

    players = game_data['players']
    num_questions = game_data['num_questions']
    current_question = game_data['current_question']

    # Vérifier si la partie est terminée
    if current_question >= num_questions:
        return redirect('multiplayer_end_game')

    # Créer la session de jeu et pré-générer les questions si ce n'est pas fait
    if game_data['game_session_id'] is None:
        # Générer un PIN unique
        pin_code = ''.join(random.choices('0123456789', k=6))
        while GameSession.objects.filter(PinCode=pin_code).exists():
            pin_code = ''.join(random.choices('0123456789', k=6))

        category_id = game_data.get('category_id')
        if category_id:
            category = Category.objects.get(pk=category_id)
        else:
            # Mode aléatoire: choisir une catégorie aléatoire pour la session
            category = Category.objects.order_by('?').first()

        game_session = GameSession.objects.create(
            PinCode=pin_code,
            Category=category,
            Difficulty=2,  # Difficulté moyenne par défaut
        )
        game_data['game_session_id'] = game_session.id

        # Pré-générer toutes les questions uniques
        questions_list = []
        generated_count = 0
        max_attempts = num_questions * 3  # Limiter les tentatives pour éviter les boucles infinies
        attempts = 0

        while len(questions_list) < num_questions and attempts < max_attempts:
            attempts += 1
            try:
                if game_data['is_random']:
                    # Mode aléatoire: générer depuis différentes catégories
                    random_category = Category.objects.order_by('?').first()
                    question = generate_and_save_question(random_category.descriptor, difficulty=2)
                else:
                    # Catégorie spécifique
                    question = generate_and_save_question(category.descriptor, difficulty=2)

                if question and question.pk not in [q['id'] for q in questions_list]:
                    questions_list.append({
                        'id': question.pk,
                        'text': question.text,
                        'answers': [
                            {'id': ans.pk, 'text': ans.text, 'is_correct': ans.IsCorrect}
                            for ans in question.answers.all()
                        ]
                    })
            except Exception as e:
                print(f"Erreur lors de la génération de question: {e}")
                continue

        if len(questions_list) < num_questions:
            # Si on n'a pas assez de questions, utiliser celles existantes
            existing_questions = []
            if game_data['is_random']:
                existing_questions = list(QuizQuestion.objects.order_by('?')[:num_questions])
            else:
                existing_questions = list(QuizQuestion.objects.filter(Category=category).order_by('?')[:num_questions])

            for q in existing_questions:
                if len(questions_list) >= num_questions:
                    break
                if q.pk not in [quest['id'] for quest in questions_list]:
                    questions_list.append({
                        'id': q.pk,
                        'text': q.text,
                        'answers': [
                            {'id': ans.pk, 'text': ans.text, 'is_correct': ans.IsCorrect}
                            for ans in q.answers.all()
                        ]
                    })

        game_data['questions'] = questions_list
        request.session['multiplayer_game'] = game_data
        request.session.modified = True

    game_session = GameSession.objects.get(pk=game_data['game_session_id'])
    questions_list = game_data['questions']

    # Vérifier que nous avons assez de questions
    if current_question >= len(questions_list):
        return redirect('multiplayer_end_game')

    # Obtenir la question actuelle
    current_question_data = questions_list[current_question]
    question = QuizQuestion.objects.get(pk=current_question_data['id'])

    # Déterminer le joueur actuel basé sur le numéro de question
    current_player_index = current_question % len(players)
    current_player = players[current_player_index]

    answers = current_question_data['answers']
    random.shuffle(answers)

    # Gestion de la soumission de réponse
    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer_id')

        try:
            selected_answer = Answer.objects.get(pk=selected_answer_id)
            is_correct = selected_answer.IsCorrect

            # Créer l'enregistrement PlayerAnswer
            PlayerAnswer.objects.create(
                Question=question,
                User=request.user,  # Utilisateur connecté (arbitraire pour multijoueur local)
                Session=game_session,
                Answer=selected_answer,
                IsCorrect=is_correct,
                ReactionTime=0,  # Non mesuré dans ce mode
            )

            # Mise à jour du score
            if is_correct:
                current_player['score'] += 10
                messages.success(request, f"✅ {current_player['name']} a marqué 10 points!")
            else:
                messages.warning(request, f"❌ {current_player['name']} a manqué la question.")

            # Passer à la question suivante
            game_data['current_question'] = current_question + 1
            request.session['multiplayer_game'] = game_data
            request.session.modified = True

            # Rediriger vers la même vue (nouvelle question)
            return redirect('multiplayer_game_start')

        except Answer.DoesNotExist:
            messages.error(request, "Réponse invalide.")

    # Rendu de la page de jeu
    context = {
        'page_title': "Partie Multijoueur",
        'players': players,
        'current_player': current_player,
        'question': question,
        'answers': answers,
        'current_question_num': current_question + 1,
        'total_questions': num_questions,
    }
    return render(request, 'multiplayer/game.html', context)


@login_required
@login_required
def multiplayer_submit_answer(request):
    """API endpoint pour soumettre une réponse via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    game_data = request.session.get('multiplayer_game')
    if not game_data:
        return JsonResponse({'error': 'No game in progress'}, status=400)

    players = game_data['players']
    num_questions = game_data['num_questions']
    current_question = game_data['current_question']

    if current_question >= num_questions:
        return JsonResponse({'redirect': reverse('multiplayer_end_game')})

    selected_answer_id = request.POST.get('answer_id')
    if not selected_answer_id:
        return JsonResponse({'error': 'No answer selected'}, status=400)

    try:
        selected_answer = Answer.objects.get(pk=selected_answer_id)
        question = QuizQuestion.objects.get(pk=game_data['questions'][current_question]['id'])
        game_session = GameSession.objects.get(pk=game_data['game_session_id'])

        is_correct = selected_answer.IsCorrect

        # Créer l'enregistrement PlayerAnswer
        PlayerAnswer.objects.create(
            Question=question,
            User=request.user,
            Session=game_session,
            Answer=selected_answer,
            IsCorrect=is_correct,
            ReactionTime=0,
        )

        # Déterminer le joueur actuel
        current_player_index = current_question % len(players)
        current_player = players[current_player_index]

        # Mise à jour du score
        if is_correct:
            current_player['score'] += 10

        # Passer à la question suivante
        game_data['current_question'] = current_question + 1
        game_data['players'][current_player_index] = current_player
        request.session['multiplayer_game'] = game_data
        request.session.modified = True

        # Vérifier si la partie est terminée
        if game_data['current_question'] >= num_questions:
            return JsonResponse({'redirect': reverse('multiplayer_end_game')})

        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'current_player': current_player['name'],
            'score': current_player['score'],
            'next_question': game_data['current_question'] + 1,
            'total_questions': num_questions
        })

    except (Answer.DoesNotExist, QuizQuestion.DoesNotExist, GameSession.DoesNotExist):
        return JsonResponse({'error': 'Invalid data'}, status=400)


@login_required
@login_required
def multiplayer_end_game(request):
    """Affiche l'écran de fin de partie avec les scores et sauvegarde en base."""
    game_data = request.session.get('multiplayer_game')

    if not game_data:
        messages.error(request, "Aucune partie terminée.")
        return redirect('main_menu')

    players = game_data['players']
    game_session = GameSession.objects.get(pk=game_data['game_session_id'])

    # Trier les joueurs par score décroissant
    sorted_players = sorted(players, key=lambda p: p['score'], reverse=True)
    winner = sorted_players[0]

    # Sauvegarder les scores en base de données pour chaque joueur
    # Note: En multijoueur local, tous les scores sont associés à l'utilisateur connecté
    # mais nous différencions par session et pourrions ajouter un champ pour le nom du joueur
    for player in players:
        PlayerScore.objects.create(
            Session=game_session,
            User=request.user,  # Utilisateur connecté qui a organisé la partie
            Score=player['score'],
        )

    # Nettoyer la session
    del request.session['multiplayer_game']
    request.session.modified = True

    context = {
        'page_title': "Fin de Partie",
        'players': sorted_players,
        'winner': winner,
        'game_session': game_session,
    }
    return render(request, 'multiplayer/end_game.html', context)



@login_required
@login_required
def classements_view(request):
    """Page des classements globaux."""
    # Récupérer les meilleurs scores de toutes les sessions
    top_scores = PlayerScore.objects.select_related('User', 'Session__Category').order_by('-Score')[:50]
    
    # Grouper par utilisateur pour obtenir les meilleurs scores individuels
    user_best_scores = {}
    for score in top_scores:
        user_id = score.User.id
        if user_id not in user_best_scores or score.Score > user_best_scores[user_id]['score']:
            user_best_scores[user_id] = {
                'user': score.User,
                'score': score.Score,
                'session': score.Session,
                'time': score.Time,
            }
    
    # Trier par score décroissant
    rankings = sorted(user_best_scores.values(), key=lambda x: x['score'], reverse=True)[:20]
    
    context = {
        'rankings': rankings,
        'page_title': "Classements Globaux"
    }
    return render(request, 'classements.html', context)



@csrf_protect
def register_view(request):
    """Page d'inscription."""
    # (Logique de gestion du formulaire d'inscription non modifiée)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('confirm_password', '').strip()

        errors = {}

        if not username: errors['username'] = 'Le nom d\'utilisateur est requis.'
        elif len(username) < 3: errors['username'] = 'Le nom d\'utilisateur doit contenir au moins 3 caractères.'
        if not email: errors['email'] = 'L\'email est requis.'
        elif '@' not in email: errors['email'] = 'L\'email doit être valide.'
        if not password: errors['password'] = 'Le mot de passe est requis.'
        elif len(password) < 8: errors['password'] = 'Le mot de passe doit contenir au moins 8 caractères.'
        if password != password_confirm: errors['confirm_password'] = 'Les mots de passe ne correspondent pas.'

        if username and User.objects.filter(username=username).exists():
            errors['username'] = 'Ce nom d\'utilisateur existe déjà.'
        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'Cet email est déjà utilisé.'

        if errors:
            return render(request, 'register.html', {'errors': errors, 'username': username, 'email': email})

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f'Compte créé avec succès ! Bienvenue {username}.')
            login(request, user)
            return redirect('main_menu')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
            return render(request, 'register.html', {'errors': {}, 'username': username, 'email': email})

    return render(request, 'register.html', {'errors': {}})



@login_required(login_url='/')
def profile_view(request):
    """Affiche le profil de l'utilisateur connecté."""
    return render(request, 'profile.html', {'user': request.user})

@login_required(login_url='/')
def logout_view(request):
    """Termine la session utilisateur et redirige vers la page de connexion."""
    logout(request)
    return redirect('/')

# =================================================================
# ===== II. VUES API (Django Rest Framework) =====
# =================================================================
# (Ces classes API n'ont pas été modifiées)

class RegisterAPIView(APIView):
    """API pour créer un compte : POST /api/auth/register/"""
    permission_classes = [permissions.AllowAny] 

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'message': 'Compte créé avec succès', 'user': UserSerializer(user).data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    """API pour se connecter : POST /api/auth/login/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return Response(
                    {'message': 'Connecté avec succès', 'user': UserSerializer(user).data},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'error': 'Nom d\'utilisateur ou mot de passe incorrect'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeAPIView(APIView):
    """API pour récupérer l'utilisateur connecté : GET /api/auth/me/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response({'error': 'Non authentifié'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    """API pour se déconnecter : POST /api/auth/logout/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Déconnecté avec succès'}, status=status.HTTP_200_OK)

class PlayerScoreViewSet(viewsets.ModelViewSet):
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer

class PlayerAnswerViewSet(viewsets.ModelViewSet):
    queryset = PlayerAnswer.objects.all()
    serializer_class = PlayerAnswerSerializer

class QuizQuestionViewSet(viewsets.ModelViewSet):
    queryset = QuizQuestion.objects.all()
    serializer_class = QuizQuestionSerializer

class GameSessionViewSet(viewsets.ModelViewSet):
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return self.serializer_class