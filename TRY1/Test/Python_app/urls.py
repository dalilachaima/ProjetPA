from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'player-scores', views.PlayerScoreViewSet)
router.register(r'player-answers', views.PlayerAnswerViewSet)
router.register(r'quiz-questions', views.QuizQuestionViewSet)
router.register(r'game-sessions', views.GameSessionViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('api/', include(router.urls)),
]