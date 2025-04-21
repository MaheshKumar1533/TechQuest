# techquest/quest/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    secret_code = models.CharField(max_length=100, unique=True)
    total_rounds = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Round(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    round_number = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    min_qualify_marks = models.FloatField(default=0)

    class Meta:
        unique_together = ('quiz', 'round_number')

    def __str__(self):
        return f"{self.quiz.title} - Round {self.round_number}"

class Question(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    text = models.TextField()
    correct_option = models.CharField(max_length=255)
    other_options = models.JSONField(default=list)
    marks = models.FloatField(default=1.0)
    image = models.ImageField(upload_to='questions/', blank=True, null=True)

    def __str__(self):
        return self.text

class UserQuiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    current_round = models.PositiveIntegerField(default=1)
    total_score = models.FloatField(default=0.0)
    total_time_taken = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"

class UserResponse(models.Model):
    user_quiz = models.ForeignKey(UserQuiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=255, null=True, blank=True)
    time_taken = models.FloatField(default=0.0)
    marks_awarded = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user_quiz.user.username} - Q{self.question.id}"
