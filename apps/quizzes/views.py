from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.enrollments.models import Enrollment
from .models import Quiz, QuizAttempt, QuizAnswer, Choice


@login_required
def take_quiz(request, course_slug, quiz_id):
    from apps.courses.models import Course
    course = get_object_or_404(Course, slug=course_slug, status='published')
    quiz = get_object_or_404(Quiz, id=quiz_id, lesson__section__course=course)

    get_object_or_404(Enrollment, student=request.user, course=course, status='active')

    # Check attempt count
    attempt_count = QuizAttempt.objects.filter(
        student=request.user, quiz=quiz, status='completed'
    ).count()

    if quiz.max_attempts > 0 and attempt_count >= quiz.max_attempts:
        messages.warning(request, f'You have used all {quiz.max_attempts} attempts for this quiz.')
        return redirect('quizzes:result', course_slug=course_slug, quiz_id=quiz_id)

    # Create new attempt
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        attempt_number=attempt_count + 1,
        max_score=sum(q.points for q in quiz.questions.all()),
    )

    questions = quiz.questions.all()
    if quiz.shuffle_questions:
        questions = questions.order_by('?')

    if request.method == 'POST':
        score = 0
        for question in quiz.questions.all():
            selected_ids = request.POST.getlist(f'question_{question.id}')
            selected_choices = Choice.objects.filter(id__in=selected_ids, question=question)

            answer = QuizAnswer.objects.create(attempt=attempt, question=question)
            answer.selected_choices.set(selected_choices)

            correct_ids = set(question.choices.filter(is_correct=True).values_list('id', flat=True))
            selected_correct = set(int(i) for i in selected_ids if i.isdigit())

            if question.question_type in ('mcq', 'true_false'):
                is_correct = selected_correct == correct_ids
            else:
                is_correct = selected_correct == correct_ids

            points_earned = question.points if is_correct else 0
            answer.is_correct = is_correct
            answer.points_earned = points_earned
            answer.save()
            score += points_earned

        attempt.score = score
        attempt.percentage = (score / attempt.max_score * 100) if attempt.max_score > 0 else 0
        attempt.passed = attempt.percentage >= quiz.pass_percentage
        attempt.status = 'completed'
        attempt.submitted_at = timezone.now()
        attempt.time_taken_seconds = int((attempt.submitted_at - attempt.started_at).total_seconds())
        attempt.save()

        return redirect('quizzes:result_attempt', course_slug=course_slug, quiz_id=quiz_id, attempt_id=attempt.id)

    return render(request, 'quizzes/take_quiz.html', {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
    })


@login_required
def quiz_result(request, course_slug, quiz_id, attempt_id=None):
    from apps.courses.models import Course
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if attempt_id:
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    else:
        attempt = QuizAttempt.objects.filter(
            student=request.user, quiz=quiz, status='completed'
        ).order_by('-started_at').first()

    all_attempts = QuizAttempt.objects.filter(
        student=request.user, quiz=quiz, status='completed'
    ).order_by('-started_at')

    return render(request, 'quizzes/quiz_result.html', {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'all_attempts': all_attempts,
    })
