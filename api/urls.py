from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [

    # ── Auth ─────────────────────────────────────────────────────
    path('login/',   views.login_view, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/',      views.me_view,    name='me'),

    # ── Student ──────────────────────────────────────────────────
    path('student/dashboard/',  views.student_dashboard,  name='student-dashboard'),
    path('student/results/',    views.student_results,    name='student-results'),
    path('student/transcript/', views.student_transcript, name='student-transcript'),
    path('student/profile/',    views.student_profile,    name='student-profile'),

    # ── Faculty ──────────────────────────────────────────────────
    path('faculty/dashboard/',                        views.faculty_dashboard, name='faculty-dashboard'),
    path('faculty/courses/',                          views.faculty_courses,   name='faculty-courses'),
    path('faculty/courses/<int:course_id>/students/', views.course_students,   name='course-students'),
    path('faculty/grades/',                           views.submit_grades,     name='submit-grades'),

    # ── Admin (renamed to avoid conflict with Django's built-in admin) ──
    path('portal/dashboard/',           views.admin_dashboard,     name='admin-dashboard'),
    path('portal/students/',            views.admin_students,      name='admin-students'),
    path('portal/faculty/',             views.admin_faculty,       name='admin-faculty'),
    path('portal/results/unpublished/', views.unpublished_results, name='unpublished-results'),
    path('portal/results/publish/',     views.publish_results,     name='publish-results'),
    path('portal/notices/',             views.notice_create,       name='notice-create'),
    path('portal/notices/<int:pk>/',    views.notice_update,       name='notice-update'),

    # ── Public ───────────────────────────────────────────────────
    path('notices/',          views.notice_list,   name='notice-list'),
    path('notices/<int:pk>/', views.notice_detail, name='notice-detail'),
]