from django.shortcuts import render
<<<<<<< HEAD
from django.http import HttpResponse
from rest_framework import viewsets
from .models import PlayerScore, PlayerAnswer, QuizQuestion, GameSession, User
from .serializers import PlayerScoreSerializer, PlayerAnswerSerializer, QuizQuestionSerializer, GameSessionSerializer, UserSerializer,LoginSerializer,UserRegistrationSerializer
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth import authenticate, login, logout

def home(request):
    return HttpResponse("Bienvenue sur la page d'accueil! <a href='/accounts/login/'>Se connecter</a>")


# --- Existing Model ViewSets ---

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

# --- MODIFIED UserViewSet (For Secure Registration) ---
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    # Overrides the default serializer logic
    def get_serializer_class(self):
        """
        Uses UserRegistrationSerializer for POST (creation) requests, 
        and UserSerializer for all others (GET, PUT, etc.).
        """
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return self.serializer_class

# --- NEW API AUTHENTICATION ENDPOINTS ---

# 1. Login: POST /api/auth/login
class LoginAPIView(APIView):
    # This endpoint is accessible by anyone
    permission_classes = [permissions.AllowAny] 
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        # Raises an exception (400 Bad Request) if data is invalid
        serializer.is_valid(raise_exception=True) 
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Use Django's authenticate to check credentials
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # If valid, start a session and set the session cookie
            login(request, user) 
            # Return the user data using the safe UserSerializer
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

# 2. Auto-login Check: GET /api/auth/me
class MeAPIView(APIView):
    # Only logged-in users can access this
    permission_classes = [permissions.IsAuthenticated] 
    
    def get(self, request):
        # request.user is automatically populated by Django's session middleware
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

# 3. Logout: POST /api/auth/logout
class LogoutAPIView(APIView):
    # Requires authentication to log out
    permission_classes = [permissions.IsAuthenticated] 
    
    def post(self, request):
        # Terminate the current session
        logout(request) 
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
=======

# Create your views here.
>>>>>>> 2c823b1e00dbe02827fcab2b690cf9d18c5eafb3
