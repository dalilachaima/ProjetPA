from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import PlayerScore, PlayerAnswer, QuizQuestion, GameSession, Answer, Category,User

class PlayerScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerScore
        fields = '__all__'

class PlayerAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerAnswer
        fields = '__all__'

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = '__all__'

class GameSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSession
        fields = '__all__'

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
class UserSerializer(serializers.ModelSerializer):
    """Serializer for GET/PUT/PATCH requests (read/update user data)"""
    class Meta:
        model = User
        fields = ('id', 'username', 'ControlTimestamp')
        read_only_fields = ('ControlTimestamp',) 


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for POST requests (create new user)"""
    
    # Password remains write_only for security
    password = serializers.CharField(write_only=True) 

    class Meta:
        model = User
        # Fields now only require username and password
        fields = ('username', 'password') 
        
    def create(self, validated_data):
        # 1. Extract the plain password
        plain_password = validated_data.pop('password')
        
        # 2. Create the User object (only username is left in validated_data)
        user = User.objects.create(**validated_data)
        
        # 3. Hash the password and save it
        user.passwordHash = make_password(plain_password)
        
        user.save()
        return user
class LoginSerializer(serializers.Serializer):
    """Serializer used to validate POST data for the login endpoint."""
    username = serializers.CharField(required=True)
    # Password must be write-only for security, but NOT a ModelSerializer field
    password = serializers.CharField(required=True, write_only=True)