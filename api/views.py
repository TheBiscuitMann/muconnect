from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Student, Faculty, Course, Enrollment, Result, Notice, User
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
    return Response({
        'student_id':       student.student_id,
        'name':             request.user.get_full_name(),
        'department':       student.department.name,
        'batch':            student.batch,
        'current_semester': student.current_semester,
        'cgpa':             float(student.cgpa),
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

    return Response({
        'student': {
            'name':       request.user.get_full_name(),
            'student_id': student.student_id,
            'department': student.department.name,
            'batch':      student.batch,
            'cgpa':       float(student.cgpa),
        },
        'results': ResultSerializer(
            [e.result for e in enrollments], many=True
        ).data,
    })


# ── Faculty ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsFaculty])
def faculty_courses(request):
    faculty = request.user.faculty
    courses = Course.objects.filter(faculty=faculty)
    return Response(CourseSerializer(courses, many=True).data)


@api_view(['GET'])
@permission_classes([IsFaculty])
def course_students(request, course_id):
    try:
        course = Course.objects.get(id=course_id, faculty=request.user.faculty)
    except Course.DoesNotExist:
        return Response({'message': 'Course not found'}, status=404)

    enrollments = Enrollment.objects.filter(
        course=course
    ).select_related('student__user', 'result')

    data = []
    for e in enrollments:
        entry = {
            'enrollment_id': e.id,
            'student_id':    e.student.student_id,
            'name':          e.student.user.get_full_name(),
            'marks':         None,
            'grade':         None,
            'grade_point':   None,
            'published':     False,
        }
        if hasattr(e, 'result'):
            entry['marks']       = float(e.result.marks or 0)
            entry['grade']       = e.result.grade
            entry['grade_point'] = float(e.result.grade_point or 0)
            entry['published']   = e.result.published
        data.append(entry)

    return Response(data)


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
        'unpublished_results': Result.objects.filter(published=False).count(),
        'active_notices':      Notice.objects.filter(is_active=True).count(),
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def unpublished_results(request):
    results = Result.objects.filter(published=False).select_related(
        'enrollment__student__user',
        'enrollment__course',
    )
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
    notices  = Notice.objects.filter(is_active=True)
    if category:
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