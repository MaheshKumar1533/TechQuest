# techviews.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Quiz, Round, Question, UserQuiz, UserResponse
from django.http import JsonResponse
import time
from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Round, UserQuiz
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from .models import Round, Quiz, UserQuiz

from django.shortcuts import render, get_object_or_404, redirect
from .models import Quiz, Round, UserQuiz
from django.contrib.auth.decorators import login_required

@login_required
def enter_secret_code(request):
    quizzes = Quiz.objects.filter(is_active=True)

    if request.method == 'POST':
        code = request.POST.get('secret_code')
        quiz_id = request.POST.get('quiz_id')

        if not quiz_id:
            return render(request, 'enter_code.html', {'quizzes': quizzes, 'error': 'Please select a quiz.'})

        quiz = Quiz.objects.filter(id=quiz_id, secret_code=code, is_active=True).first()

        if quiz:
            # Check if the quiz is completed and the code is valid
            if quiz.end_time < timezone.now():
                return render(request, 'enter_code.html', {'quizzes': quizzes, 'error': 'This quiz has already ended.'})
            print(f"Quiz found: {quiz.title}, Start: {quiz.start_time}, End: {quiz.end_time}")

            round_obj = Round.objects.filter(quiz=quiz, round_number=1).first()
            if not round_obj:
                return render(request, 'enter_code.html', {'quizzes': quizzes, 'error': 'Round 1 not found in this quiz.'})

            user_quiz, created = UserQuiz.objects.get_or_create(user=request.user, quiz=quiz)
            print(f"User Quiz created: {created}, Current Round: 1")

            return redirect('show_instructions', quiz_id=quiz.id, round_number=1)

        else:
            return render(request, 'enter_code.html', {'quizzes': quizzes, 'error': 'Invalid or inactive secret code.'})

    return render(request, 'enter_code.html', {'quizzes': quizzes})







def show_instructions(request, quiz_id, round_number):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    round_obj = get_object_or_404(Round, quiz=quiz, round_number=round_number)

    # Calculate the remaining time until the quiz starts
    remaining_time = quiz.start_time - timezone.now()
    if remaining_time.total_seconds() > 0:
        minutes = remaining_time.seconds // 60
        seconds = remaining_time.seconds % 60
    else:
        minutes = seconds = 0  # The quiz has already started, handle accordingly

    return render(request, 'instructions.html', {
        'quiz': quiz,
        'round': round_obj,
        'remaining_time': remaining_time,
        'minutes': minutes,
        'seconds': seconds
    })




import random
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def start_round(request, quiz_id, round_number):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    round_obj = get_object_or_404(Round, quiz=quiz, round_number=round_number)
    questions = Question.objects.filter(round=round_obj)
    user_quiz, _ = UserQuiz.objects.get_or_create(user=request.user, quiz=quiz)
    user_quiz.current_round = round_number

    # Shuffle and attach options
    for question in questions:
        options = question.other_options.copy()
        options.append(question.correct_option)
        random.shuffle(options)
        question.shuffled_options = options

    # Handle POST submission
    if request.method == 'POST':
        for question in questions:
            selected = request.POST.get(f'question_{question.id}')
            time_taken = float(request.POST.get(f'time_taken_{question.id}', 0))
            marks = question.marks if selected == question.correct_option else 0

            UserResponse.objects.update_or_create(
                user_quiz=user_quiz,
                question=question,
                defaults={
                    'selected_option': selected,
                    'marks_awarded': marks,
                    'time_taken': time_taken,
                }
            )

        # Update score
        round_responses = UserResponse.objects.filter(user_quiz=user_quiz, question__round=round_obj)
        round_score = sum(resp.marks_awarded for resp in round_responses)
        user_quiz.total_score += round_score
        user_quiz.current_round += 1
        user_quiz.save()

        # If all rounds done
        print(user_quiz.current_round, quiz.total_rounds)
        if user_quiz.current_round > quiz.total_rounds:
            user_quiz.is_completed = True
            user_quiz.end_time = timezone.now()
            user_quiz.total_time_taken = (user_quiz.end_time - user_quiz.start_time).total_seconds()
            user_quiz.save()
            return redirect('dashboard')

        # Redirect to next round
        print("redirecting to next round")
        return redirect('show_instructions', quiz_id=quiz.id, round_number=user_quiz.current_round)

    # Start timer if not already started
    if not user_quiz.start_time:
        user_quiz.start_time = timezone.now()
        user_quiz.save()

    return render(request, 'quiz_round.html', {
        'quiz': quiz,
        'round': round_obj,
        'questions': questions,
        'end_time': quiz.end_time.isoformat()
    })



from django.db.models import Count, Sum, Q
from django.db import models


@login_required
def dashboard(request):
    user_quizzes = UserQuiz.objects.filter(user=request.user)

    # Enrich data per quiz
    enriched_quizzes = []
    for quiz in user_quizzes:
        responses = UserResponse.objects.filter(user_quiz=quiz)

        total_questions_attempted = responses.count()
        correct_answers = responses.filter(
            selected_option=models.F('question__correct_option')
        ).count()
        total_rounds_attempted = responses.values('question__round').distinct().count()

        enriched_quizzes.append({
            'quiz': quiz,
            'questions_attempted': total_questions_attempted,
            'correct_answers': correct_answers,
            'rounds_attempted': total_rounds_attempted,
        })

    return render(request, 'dashboard.html', {'enriched_quizzes': enriched_quizzes})



def leaderboard(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    participants = UserQuiz.objects.filter(quiz=quiz, is_completed=True, is_approved=True)
    ranked = sorted(participants, key=lambda u: (-u.total_score, u.total_time_taken))
    return render(request, 'leaderboard.html', {'quiz': quiz, 'participants': ranked})

import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Quiz, Round, Question

def upload_questions_csv(request):
    quizzes = Quiz.objects.all()
    rounds = Round.objects.all()

    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')
        round_id = request.POST.get('round_id')
        csv_file = request.FILES.get('csv_file')

        if not (quiz_id and round_id and csv_file):
            messages.error(request, "All fields are required.")
            return redirect('upload_questions_csv')

        try:
            round_obj = Round.objects.get(id=round_id, quiz_id=quiz_id)
        except Round.DoesNotExist:
            messages.error(request, "Selected round not found.")
            return redirect('upload_questions_csv')

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        for row in reader:
            if len(row) < 6:
                continue  # skip invalid rows
            question_text, correct_option, *other_options = row
            Question.objects.create(
                round=round_obj,
                text=question_text.strip(),
                correct_option=correct_option.strip(),
                other_options=[opt.strip() for opt in other_options],
            )

        messages.success(request, "Questions uploaded successfully!")
        return redirect('upload_questions_csv')

    return render(request, 'upload_questions.html', {'quizzes': quizzes, 'rounds': rounds})
