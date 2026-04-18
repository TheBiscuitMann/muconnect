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

    # ── Retake ───────────────────────────────────────────────────
    path('student/retake/apply/',        views.apply_retake,           name='retake-apply'),
    path('student/retake/applications/', views.my_retake_applications, name='my-retake-apps'),

    # ── Peer Network ─────────────────────────────────────────────
    path('student/peer/status/',                         views.peer_status,             name='peer-status'),
    path('student/peer/toggle/',                         views.peer_toggle_mentor,      name='peer-toggle'),
    path('student/peer/mentors/',                        views.peer_mentors,            name='peer-mentors'),
    path('student/peer/conversations/',                  views.peer_conversations,      name='peer-conversations'),
    path('student/peer/start/',                          views.peer_start_conversation, name='peer-start'),
    path('student/peer/messages/<int:conversation_id>/', views.peer_messages,           name='peer-messages'),

    # ── Faculty ──────────────────────────────────────────────────
    path('faculty/dashboard/',                        views.faculty_dashboard,           name='faculty-dashboard'),
    path('faculty/courses/',                          views.faculty_courses,             name='faculty-courses'),
    path('faculty/courses/<int:course_id>/students/', views.course_students,             name='course-students'),
    path('faculty/grades/',                           views.submit_grades,               name='submit-grades'),
    path('faculty/retake/',                           views.faculty_retake_applications, name='faculty-retakes'),
    path('faculty/retake/<int:app_id>/',              views.faculty_update_retake,       name='faculty-retake-update'),

    # ── Attendance ───────────────────────────────────────────────
    path('faculty/attendance/batches/',                        views.attendance_batches,         name='attendance-batches'),
    path('faculty/attendance/batches/<str:batch>/courses/',    views.attendance_courses,         name='attendance-courses'),
    path('faculty/attendance/courses/<int:course_id>/sessions/',     views.attendance_sessions,        name='attendance-sessions'),
    path('faculty/attendance/courses/<int:course_id>/sessions/new/', views.attendance_create_session,  name='attendance-create'),
    path('faculty/attendance/courses/<int:course_id>/summary/',      views.attendance_summary,         name='attendance-summary'),
    path('faculty/attendance/sessions/<int:session_id>/',            views.attendance_session_detail,  name='attendance-detail'),
    path('faculty/attendance/sessions/<int:session_id>/update/',     views.attendance_update_session,  name='attendance-update'),
    path('faculty/attendance/sessions/<int:session_id>/delete/',     views.attendance_delete_session,  name='attendance-delete'),

    # ── Admin ────────────────────────────────────────────────────
    path('portal/dashboard/',                 views.admin_dashboard,     name='admin-dashboard'),
    path('portal/students/',                  views.admin_students,      name='admin-students'),
    path('portal/students/<int:student_id>/', views.admin_edit_student,  name='admin-edit-student'),
    path('portal/faculty/',                   views.admin_faculty,       name='admin-faculty'),
    path('portal/results/unpublished/',       views.unpublished_results, name='unpublished-results'),
    path('portal/results/publish/',           views.publish_results,     name='publish-results'),
    path('portal/notices/',                   views.notice_create,       name='notice-create'),
    path('portal/notices/<int:pk>/',          views.notice_update,       name='notice-update'),

    # ── Public ───────────────────────────────────────────────────
    path('notices/',          views.notice_list,   name='notice-list'),
    path('notices/<int:pk>/', views.notice_detail, name='notice-detail'),
]