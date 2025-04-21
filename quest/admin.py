from django.contrib import admin
from .models import Quiz, UserQuiz, Question, UserResponse, Round

# Register your models here.
admin.site.register(Quiz)
admin.site.register(UserQuiz)
admin.site.register(Question)
admin.site.register(UserResponse)
admin.site.register(Round)
