from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views 

# Initialize the router for ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet) 
router.register(r'player-scores', views.PlayerScoreViewSet)
router.register(r'player-answers', views.PlayerAnswerViewSet)
router.register(r'quiz-questions', views.QuizQuestionViewSet)
router.register(r'game-sessions', views.GameSessionViewSet)

# Define the URL patterns
urlpatterns = [
    # 1. API AUTHENTICATION ROUTES (Individual paths for APIViews)
    path('api/auth/login/', views.LoginAPIView.as_view(), name='api-login'),
    path('api/auth/me/', views.MeAPIView.as_view(), name='api-me'),
    path('api/auth/logout/', views.LogoutAPIView.as_view(), name='api-logout'),

    path('api/', include(router.urls)),
    path('', views.home, name='home'),
]