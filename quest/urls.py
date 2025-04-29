
# techquest/quest/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.logUsr, name='logUsr'),
    path('entercode', views.enter_secret_code, name='enter_secret_code'),
    path('quiz/<int:quiz_id>/round/<int:round_number>/instructions/', views.show_instructions, name='show_instructions'),
    path('quiz/<int:quiz_id>/round/<int:round_number>/', views.start_round, name='start_round'),
    path('quiz/<int:quiz_id>/round/select/', views.enter_secret_code, name='select_round'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('leaderboard/<int:quiz_id>/', views.leaderboard, name='leaderboard'),
    path('upload-questions/', views.upload_questions_csv, name='upload_questions_csv'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)