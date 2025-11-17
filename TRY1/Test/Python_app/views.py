from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets
from .models import PlayerScore, PlayerAnswer, QuizQuestion, GameSession
from .serializers import PlayerScoreSerializer, PlayerAnswerSerializer, QuizQuestionSerializer, GameSessionSerializer


def home(request):
    return HttpResponse("Bienvenue sur la page d'accueil! <a href='/accounts/login/'>Se connecter</a>")


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