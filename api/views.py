from django.utils import timezone
from django.db import models as django_models
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Student, Faculty, Course, Enrollment, Result, Notice, User, Conversation, Message
from .serializers import (
    StudentSerializer, FacultySerializer, CourseSerializer,
    ResultSerializer, NoticeSerializer, GradeSubmitSerializer, UserSerializer
)
from .permissions import IsStudent, IsFaculty, IsAdmin


# ── Auth ──────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email    = request.data.get('email')
    password = request.data.get('password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'Invalid credentials'}, status=401)

    if not user.check_password(password):
        return Response({'message': 'Invalid credentials'}, status=401)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id':    user.id,
            'name':  user.get_full_name(),
            'email': user.email,
            'role':  user.role,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user    = request.user
    profile = None
    if user.role == 'student':
        try:    profile = StudentSerializer(user.student).data
        except: pass
    elif user.role == 'faculty':
        try:    profile = FacultySerializer(user.faculty).data
        except: pass
    return Response({'user': UserSerializer(user).data, 'profile': profile})


# ── Student ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsStudent])
def student_dashboard(request):
    student = request.user.student

    all_enrollments = Enrollment.objects.filter(student=student)
    published = all_enrollments.filter(
        result__published=True
    ).select_related('course', 'result')

    total_courses  = all_enrollments.count()
    passed_courses = published.exclude(result__grade='F').count()
    failed_courses = published.filter(result__grade='F').count()
    credits_earned = sum(
        e.course.credit for e in published if e.result.grade != 'F'
    )

    total_credits_required = Course.objects.filter(
        department=student.department
    ).aggregate(total=django_models.Sum('credit'))['total'] or 160

    degree_progress = round(
        (credits_earned / total_credits_required) * 100, 1
    ) if total_credits_required else 0

    recent_notices = Notice.objects.filter(
        is_active=True
    ).order_by('-published_at')[:3]

    notices_data = [{
        'id':           n.id,
        'title':        n.title,
        'category':     n.category,
        'published_at': n.published_at,
    } for n in recent_notices]

    return Response({
        'student_id':             student.student_id,
        'name':                   request.user.get_full_name(),
        'department':             student.department.name,
        'batch':                  student.batch,
        'current_semester':       student.current_semester,
        'cgpa':                   float(student.cgpa),
        'total_courses':          total_courses,
        'passed_courses':         passed_courses,
        'failed_courses':         failed_courses,
        'credits_earned':         credits_earned,
        'total_credits_required': total_credits_required,
        'degree_progress':        degree_progress,
        'recent_notices':         notices_data,
    })


@api_view(['GET'])
@permission_classes([IsStudent])
def student_results(request):
    student     = request.user.student
    enrollments = Enrollment.objects.filter(
        student=student,
        result__published=True
    ).select_related('course', 'result')

    semesters = {}
    for enrollment in enrollments:
        sem = enrollment.semester
        if sem not in semesters:
            semesters[sem] = {'semester': sem, 'courses': [], 'gpa': 0}
        semesters[sem]['courses'].append({
            'code':        enrollment.course.code,
            'title':       enrollment.course.title,
            'credit':      enrollment.course.credit,
            'marks':       float(enrollment.result.marks or 0),
            'grade':       enrollment.result.grade,
            'grade_point': float(enrollment.result.grade_point or 0),
        })

    for sem_data in semesters.values():
        total_points  = sum(c['grade_point'] * c['credit'] for c in sem_data['courses'])
        total_credits = sum(c['credit'] for c in sem_data['courses'])
        sem_data['gpa'] = round(total_points / total_credits, 2) if total_credits else 0

    return Response({
        'cgpa':      float(student.cgpa),
        'semesters': list(semesters.values()),
    })


@api_view(['GET'])
@permission_classes([IsStudent])
def student_transcript(request):
    student     = request.user.student
    enrollments = Enrollment.objects.filter(
        student=student,
        result__published=True
    ).select_related('course', 'result').order_by('semester')

    semesters = {}
    for e in enrollments:
        sem = e.semester
        if sem not in semesters:
            semesters[sem] = {
                'semester': sem,
                'year':     e.year,
                'courses':  [],
                'gpa':      0,
            }
        semesters[sem]['courses'].append({
            'code':        e.course.code,
            'title':       e.course.title,
            'credit':      e.course.credit,
            'marks':       float(e.result.marks or 0),
            'grade':       e.result.grade,
            'grade_point': float(e.result.grade_point or 0),
        })

    for sem_data in semesters.values():
        total_points  = sum(c['grade_point'] * c['credit'] for c in sem_data['courses'])
        total_credits = sum(c['credit'] for c in sem_data['courses'])
        sem_data['gpa'] = round(total_points / total_credits, 2) if total_credits else 0

    credits_earned = sum(
        e.course.credit for e in enrollments if e.result.grade != 'F'
    )

    return Response({
        'student': {
            'name':             request.user.get_full_name(),
            'student_id':       student.student_id,
            'department':       student.department.name,
            'batch':            student.batch,
            'current_semester': student.current_semester,
            'cgpa':             float(student.cgpa),
            'credits_earned':   credits_earned,
        },
        'semesters': list(semesters.values()),
    })


@api_view(['GET', 'PUT'])
@permission_classes([IsStudent])
def student_profile(request):
    student = request.user.student
    user    = request.user

    if request.method == 'GET':
        return Response({
            'name':             user.get_full_name(),
            'first_name':       user.first_name,
            'last_name':        user.last_name,
            'email':            user.email,
            'student_id':       student.student_id,
            'department':       student.department.name,
            'batch':            student.batch,
            'current_semester': student.current_semester,
            'cgpa':             float(student.cgpa),
            'phone':            student.phone or '',
        })

    elif request.method == 'PUT':
        first_name = request.data.get('first_name')
        last_name  = request.data.get('last_name')
        phone      = request.data.get('phone')

        if first_name: user.first_name = first_name
        if last_name:  user.last_name  = last_name
        user.save()

        if phone is not None:
            student.phone = phone
            student.save()

        return Response({'message': 'Profile updated successfully'})


# ── Faculty ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsFaculty])
def faculty_dashboard(request):
    faculty = request.user.faculty
    courses = Course.objects.filter(faculty=faculty)

    total_students = Enrollment.objects.filter(
        course__in=courses
    ).values('student').distinct().count()

    pending_grades = Enrollment.objects.filter(
        course__in=courses
    ).exclude(result__isnull=False).count()

    return Response({
        'name':           request.user.get_full_name(),
        'faculty_id':     faculty.faculty_id,
        'department':     faculty.department.name,
        'designation':    faculty.designation,
        'total_courses':  courses.count(),
        'total_students': total_students,
        'pending_grades': pending_grades,
    })


@api_view(['GET'])
@permission_classes([IsFaculty])
def faculty_courses(request):
    faculty = request.user.faculty
    courses = Course.objects.filter(faculty=faculty).select_related('department')

    data = []
    for c in courses:
        enrolled = Enrollment.objects.filter(course=c).count()
        graded   = Enrollment.objects.filter(course=c, result__isnull=False).count()
        data.append({
            'id':         c.id,
            'code':       c.code,
            'title':      c.title,
            'credit':     c.credit,
            'semester':   c.semester,
            'department': c.department.name,
            'enrolled':   enrolled,
            'graded':     graded,
            'pending':    enrolled - graded,
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsFaculty])
def course_students(request, course_id):
    try:
        course = Course.objects.get(id=course_id, faculty=request.user.faculty)
    except Course.DoesNotExist:
        return Response({'message': 'Course not found'}, status=404)

    enrollments = Enrollment.objects.filter(
        course=course
    ).select_related('student__user', 'student__department')

    data = []
    for e in enrollments:
        entry = {
            'enrollment_id': e.id,
            'student_id':    e.student.student_id,
            'name':          e.student.user.get_full_name(),
            'semester':      e.semester,
            'marks':         None,
            'grade':         None,
            'grade_point':   None,
            'published':     False,
        }
        try:
            r = e.result
            entry['marks']       = float(r.marks or 0)
            entry['grade']       = r.grade
            entry['grade_point'] = float(r.grade_point or 0)
            entry['published']   = r.published
        except Result.DoesNotExist:
            pass
        data.append(entry)

    return Response({
        'course': {
            'id':     course.id,
            'code':   course.code,
            'title':  course.title,
            'credit': course.credit,
        },
        'students': data,
    })


@api_view(['POST'])
@permission_classes([IsFaculty])
def submit_grades(request):
    serializer = GradeSubmitSerializer(data=request.data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    for item in serializer.validated_data:
        calculated = Result.calculate_grade(float(item['marks']))
        Result.objects.update_or_create(
            enrollment_id=item['enrollment_id'],
            defaults={
                'marks':        item['marks'],
                'grade':        calculated['grade'],
                'grade_point':  calculated['grade_point'],
                'published':    False,
                'submitted_by': request.user,
            }
        )
    return Response({'message': 'Grades submitted successfully'})


# ── Admin ─────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_dashboard(request):
    return Response({
        'total_students':      Student.objects.count(),
        'total_faculty':       Faculty.objects.count(),
        'total_courses':       Course.objects.count(),
        'total_departments':   Course.objects.values('department').distinct().count(),
        'unpublished_results': Result.objects.filter(published=False).count(),
        'published_results':   Result.objects.filter(published=True).count(),
        'active_notices':      Notice.objects.filter(is_active=True).count(),
        'total_enrollments':   Enrollment.objects.count(),
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_students(request):
    students = Student.objects.select_related('user', 'department').all()
    data = [{
        'id':               s.id,
        'student_id':       s.student_id,
        'name':             s.user.get_full_name(),
        'email':            s.user.email,
        'department':       s.department.name,
        'batch':            s.batch,
        'current_semester': s.current_semester,
        'cgpa':             float(s.cgpa),
        'is_active':        s.user.is_active,
    } for s in students]
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_faculty(request):
    faculty_list = Faculty.objects.select_related('user', 'department').all()
    data = [{
        'id':          f.id,
        'faculty_id':  f.faculty_id,
        'name':        f.user.get_full_name(),
        'email':       f.user.email,
        'department':  f.department.name,
        'designation': f.designation,
        'is_active':   f.user.is_active,
    } for f in faculty_list]
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdmin])
def unpublished_results(request):
    results = Result.objects.filter(published=False).select_related(
        'enrollment__student__user',
        'enrollment__course',
        'submitted_by',
    ).order_by('-updated_at')

    data = [{
        'result_id':    r.id,
        'student_id':   r.enrollment.student.student_id,
        'student_name': r.enrollment.student.user.get_full_name(),
        'course_code':  r.enrollment.course.code,
        'course_title': r.enrollment.course.title,
        'semester':     r.enrollment.semester,
        'marks':        float(r.marks or 0),
        'grade':        r.grade,
        'grade_point':  float(r.grade_point or 0),
        'submitted_by': r.submitted_by.get_full_name() if r.submitted_by else 'N/A',
    } for r in results]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdmin])
def publish_results(request):
    result_ids = request.data.get('result_ids', [])
    if not result_ids:
        return Response({'message': 'No result IDs provided'}, status=400)

    Result.objects.filter(id__in=result_ids).update(
        published=True,
        published_by=request.user,
        published_at=timezone.now(),
    )

    affected_students = Enrollment.objects.filter(
        result__id__in=result_ids
    ).values_list('student_id', flat=True).distinct()

    for student_id in affected_students:
        recalculate_cgpa(student_id)

    return Response({'message': f'{len(result_ids)} result(s) published successfully'})


def recalculate_cgpa(student_id: int):
    enrollments = Enrollment.objects.filter(
        student_id=student_id,
        result__published=True
    ).select_related('course', 'result')

    total_points  = 0.0
    total_credits = 0

    for e in enrollments:
        total_points  += float(e.result.grade_point) * e.course.credit
        total_credits += e.course.credit

    cgpa = round(total_points / total_credits, 2) if total_credits else 0.0
    Student.objects.filter(id=student_id).update(cgpa=cgpa)


# ── Notices ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def notice_list(request):
    category = request.query_params.get('category')
    notices  = Notice.objects.filter(is_active=True).order_by('-published_at')
    if category and category != 'all':
        notices = notices.filter(category=category)
    return Response(NoticeSerializer(notices, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def notice_detail(request, pk):
    try:
        notice = Notice.objects.get(pk=pk, is_active=True)
    except Notice.DoesNotExist:
        return Response({'message': 'Not found'}, status=404)
    return Response(NoticeSerializer(notice).data)


@api_view(['POST'])
@permission_classes([IsAdmin])
def notice_create(request):
    serializer = NoticeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAdmin])
def notice_update(request, pk):
    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return Response({'message': 'Not found'}, status=404)

    if request.method == 'DELETE':
        notice.is_active = False
        notice.save()
        return Response({'message': 'Notice deleted'})

    serializer = NoticeSerializer(notice, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


# ══════════════════════════════════════════════════════════════════
# Peer Network Feature
# ══════════════════════════════════════════════════════════════════

MENTOR_CGPA_THRESHOLD = 3.85


@api_view(['GET'])
@permission_classes([IsStudent])
def peer_status(request):
    """Tell the student if they're eligible to be a mentor and their current status."""
    student = request.user.student
    return Response({
        'cgpa':         float(student.cgpa),
        'is_mentor':    student.is_mentor,
        'is_eligible':  float(student.cgpa) >= MENTOR_CGPA_THRESHOLD,
        'threshold':    MENTOR_CGPA_THRESHOLD,
        'mentor_bio':   student.mentor_bio,
        'mentor_since': student.mentor_since,
    })


@api_view(['POST'])
@permission_classes([IsStudent])
def peer_toggle_mentor(request):
    """Toggle mentor status. Only students with CGPA >= threshold can become mentors."""
    student = request.user.student
    become  = request.data.get('become_mentor', False)
    bio     = request.data.get('mentor_bio', '')

    if become:
        if float(student.cgpa) < MENTOR_CGPA_THRESHOLD:
            return Response(
                {'message': f'You need a CGPA of {MENTOR_CGPA_THRESHOLD} or higher to become a mentor.'},
                status=400
            )
        student.is_mentor    = True
        student.mentor_bio   = bio
        student.mentor_since = timezone.now()
    else:
        student.is_mentor = False

    student.save()
    return Response({
        'message':      'Mentor status updated successfully',
        'is_mentor':    student.is_mentor,
        'mentor_bio':   student.mentor_bio,
        'mentor_since': student.mentor_since,
    })


@api_view(['GET'])
@permission_classes([IsStudent])
def peer_mentors(request):
    """List all active mentors (excluding the current user)."""
    current = request.user.student
    mentors = Student.objects.filter(
        is_mentor=True
    ).exclude(id=current.id).select_related('user', 'department').order_by('-cgpa')

    data = [{
        'id':               m.id,
        'student_id':       m.student_id,
        'name':             m.user.get_full_name(),
        'department':       m.department.name,
        'department_code':  m.department.short_code,
        'batch':            m.batch,
        'current_semester': m.current_semester,
        'cgpa':             float(m.cgpa),
        'bio':              m.mentor_bio,
        'mentor_since':     m.mentor_since,
    } for m in mentors]

    return Response(data)


@api_view(['GET'])
@permission_classes([IsStudent])
def peer_conversations(request):
    """List all conversations the current student is part of."""
    student = request.user.student

    conversations = Conversation.objects.filter(
        Q(mentor=student) | Q(mentee=student)
    ).select_related(
        'mentor__user', 'mentee__user',
        'mentor__department', 'mentee__department',
    ).prefetch_related('messages')

    data = []
    for c in conversations:
        if c.mentor == student:
            other    = c.mentee
            my_role  = 'mentor'
        else:
            other    = c.mentor
            my_role  = 'mentee'

        last_msg = c.messages.last()
        unread_count = c.messages.filter(read_at__isnull=True).exclude(sender=student).count()

        data.append({
            'id':            c.id,
            'other_student': {
                'id':         other.id,
                'student_id': other.student_id,
                'name':       other.user.get_full_name(),
                'department': other.department.name,
                'cgpa':       float(other.cgpa),
                'is_mentor':  other.is_mentor,
            },
            'my_role':       my_role,
            'last_message':  {
                'text':       last_msg.text if last_msg else None,
                'sender_me':  (last_msg.sender == student) if last_msg else False,
                'created_at': last_msg.created_at if last_msg else None,
            } if last_msg else None,
            'unread_count':  unread_count,
            'created_at':    c.created_at,
            'updated_at':    c.updated_at,
        })

    data.sort(key=lambda x: x.get('updated_at'), reverse=True)
    return Response(data)


@api_view(['POST'])
@permission_classes([IsStudent])
def peer_start_conversation(request):
    """Start a new conversation with a mentor (or return existing one)."""
    mentee    = request.user.student
    mentor_id = request.data.get('mentor_id')

    if not mentor_id:
        return Response({'message': 'mentor_id is required'}, status=400)

    try:
        mentor = Student.objects.get(id=mentor_id, is_mentor=True)
    except Student.DoesNotExist:
        return Response({'message': 'Mentor not found'}, status=404)

    if mentor.id == mentee.id:
        return Response({'message': 'You cannot message yourself'}, status=400)

    conversation, created = Conversation.objects.get_or_create(
        mentor=mentor, mentee=mentee
    )

    return Response({
        'id':          conversation.id,
        'created':     created,
        'mentor_name': mentor.user.get_full_name(),
    }, status=201 if created else 200)


@api_view(['GET', 'POST'])
@permission_classes([IsStudent])
def peer_messages(request, conversation_id):
    """GET: fetch all messages. POST: send a new message."""
    student = request.user.student

    try:
        conv = Conversation.objects.get(
            Q(id=conversation_id) & (Q(mentor=student) | Q(mentee=student))
        )
    except Conversation.DoesNotExist:
        return Response({'message': 'Conversation not found'}, status=404)

    if request.method == 'GET':
        Message.objects.filter(
            conversation=conv, read_at__isnull=True
        ).exclude(sender=student).update(read_at=timezone.now())

        messages = conv.messages.all()
        other    = conv.mentor if conv.mentee == student else conv.mentee

        return Response({
            'conversation': {
                'id':    conv.id,
                'other': {
                    'id':         other.id,
                    'student_id': other.student_id,
                    'name':       other.user.get_full_name(),
                    'department': other.department.name,
                    'cgpa':       float(other.cgpa),
                    'is_mentor':  other.is_mentor,
                },
                'my_role': 'mentor' if conv.mentor == student else 'mentee',
            },
            'messages': [{
                'id':          m.id,
                'text':        m.text,
                'sender_me':   (m.sender == student),
                'sender_name': m.sender.user.get_full_name(),
                'created_at':  m.created_at,
                'read_at':     m.read_at,
            } for m in messages],
        })

    elif request.method == 'POST':
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'message': 'Message text is required'}, status=400)

        msg = Message.objects.create(
            conversation=conv, sender=student, text=text
        )
        conv.save()

        return Response({
            'id':          msg.id,
            'text':        msg.text,
            'sender_me':   True,
            'sender_name': student.user.get_full_name(),
            'created_at':  msg.created_at,
            'read_at':     None,
        }, status=201)