from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .models import Category, QuizQuestion, Answer, PlayerScore, PlayerAnswer, GameSession
from .services import generate_and_save_question
import random

# DRF imports
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

# ===== VUES WEB (HTML) =====

def home_view(request):
    """Affiche la page d'accueil."""
    context = {'is_authenticated': request.user.is_authenticated, 'user': request.user}
    return render(request, 'home.html', context)

def offline_category_selection(request):
    """Affiche la liste des catégories pour le jeu offline."""
    default_categories = ["Géographie", "Histoire", "Sciences", "Informatique", "Islam", "Culture Générale"]
    try:
        if not Category.objects.exists():
            for name in default_categories:
                Category.objects.get_or_create(descriptor=name)
    except Exception:
        pass
    categories = Category.objects.all()
    return render(request, 'offline/category_selection.html', {'categories': categories, 'page_title': "Choisir une Catégorie"})

def offline_game_view(request, category_id):
    """Affiche une question de quiz et gère la soumission de réponse."""
    category = get_object_or_404(Category, pk=category_id)
    try:
        question = QuizQuestion.objects.filter(Category=category).order_by('?').first()
        if not question:
            question = generate_and_save_question(category.descriptor, difficulty=2)
        if not question:
            return render(request, 'error.html', {'message': 'Aucune question disponible.'})
    except Exception as e:
        return render(request, 'error.html', {'message': f'Erreur : {e}'})

    answers = list(question.answers.all())
    random.shuffle(answers)
    context = {
        'category': category, 'question': question, 'answers': answers,
        'fixed_time': 15, 'page_title': f"Quiz : {category.descriptor}",
        'submitted': False,
    }

    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer_id')
        try:
            selected_answer = Answer.objects.get(pk=selected_answer_id)
            is_correct = selected_answer.IsCorrect
            correct_answer = Answer.objects.get(Question=question, IsCorrect=True)
            context.update({
                'submitted': True,
                'is_correct': is_correct,
                'submitted_answer_id': int(selected_answer_id),
                'correct_answer_id': correct_answer.pk,
            })
        except Answer.DoesNotExist:
            pass

    return render(request, 'offline/game.html', context)

@login_required
def multiplayer_lobby_view(request):
    """Page du lobby multijoueur."""
    return HttpResponse("Page du Lobby Multijoueur (en construction)")

@login_required
def classements_view(request):
    """Page des classements."""
    return render(request, 'classements.html', {})

@csrf_protect
def register_view(request):
    """Page d'inscription - crée un compte utilisateur avec le modèle User Django."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('confirm_password', '').strip()

        errors = {}

        if not username:
            errors['username'] = 'Le nom d\'utilisateur est requis.'
        elif len(username) < 3:
            errors['username'] = 'Le nom d\'utilisateur doit contenir au moins 3 caractères.'

        if not email:
            errors['email'] = 'L\'email est requis.'
        elif '@' not in email:
            errors['email'] = 'L\'email doit être valide.'

        if not password:
            errors['password'] = 'Le mot de passe est requis.'
        elif len(password) < 8:
            errors['password'] = 'Le mot de passe doit contenir au moins 8 caractères.'

        if password != password_confirm:
            errors['confirm_password'] = 'Les mots de passe ne correspondent pas.'

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
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
            return render(request, 'register.html', {'errors': {}, 'username': username, 'email': email})

    return render(request, 'register.html', {'errors': {}})

@login_required(login_url='login')
def profile_view(request):
    """Affiche le profil de l'utilisateur connecté."""
    return render(request, 'profile.html', {'user': request.user})

# ===== VUES API (DRF) =====

class RegisterAPIView(APIView):
    """API pour créer un compte : POST /api/auth/register/"""
    permission_classes = []

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
    permission_classes = []

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

    def get(self, request):
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response({'error': 'Non authentifié'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    """API pour se déconnecter : POST /api/auth/logout/"""

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