from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Inclusion de votre application à la racine (/)
    path('', include('Python_app.urls')),
]