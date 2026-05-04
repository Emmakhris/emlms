from django.urls import path
from . import views
from apps.lessons import curriculum_views as cv

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='list'),
    path('create/', views.CourseCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.CourseUpdateView.as_view(), name='edit'),
    path('<slug:slug>/publish/', views.toggle_publish, name='toggle_publish'),
    path('<slug:slug>/review/', views.submit_review, name='submit_review'),

    # Curriculum management (instructor)
    path('<slug:slug>/curriculum/', cv.curriculum, name='curriculum'),
    path('<slug:slug>/curriculum/sections/add/', cv.add_section, name='section_add'),
    path('<slug:slug>/curriculum/sections/<int:section_id>/edit/', cv.edit_section, name='section_edit'),
    path('<slug:slug>/curriculum/sections/<int:section_id>/delete/', cv.delete_section, name='section_delete'),
    path('<slug:slug>/curriculum/sections/reorder/', cv.reorder_sections, name='sections_reorder'),
    path('<slug:slug>/curriculum/sections/<int:section_id>/lessons/add/', cv.add_lesson, name='lesson_add'),
    path('<slug:slug>/curriculum/lessons/<uuid:lesson_id>/edit/', cv.edit_lesson, name='lesson_edit'),
    path('<slug:slug>/curriculum/lessons/<uuid:lesson_id>/delete/', cv.delete_lesson, name='lesson_delete'),
    path('<slug:slug>/curriculum/sections/<int:section_id>/lessons/reorder/', cv.reorder_lessons, name='lessons_reorder'),
    path('<slug:slug>/curriculum/lessons/<uuid:lesson_id>/upload-resource/', cv.upload_resource, name='resource_upload'),
]
