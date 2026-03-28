from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Department, Student, Faculty, Course, Enrollment, Result, Notice

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Department
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    user       = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model  = Student
        fields = ['id', 'user', 'student_id', 'department',
                  'batch', 'current_semester', 'cgpa', 'phone']


class FacultySerializer(serializers.ModelSerializer):
    user       = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model  = Faculty
        fields = ['id', 'user', 'faculty_id', 'department',
                  'designation', 'specialization', 'phone']


class CourseSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    faculty    = FacultySerializer(read_only=True)

    class Meta:
        model  = Course
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):
    course_code  = serializers.CharField(source='enrollment.course.code',  read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    credit       = serializers.IntegerField(source='enrollment.course.credit', read_only=True)
    semester     = serializers.CharField(source='enrollment.semester', read_only=True)

    class Meta:
        model  = Result
        fields = ['id', 'course_code', 'course_title', 'credit',
                  'semester', 'marks', 'grade', 'grade_point', 'published']


class NoticeSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )

    class Meta:
        model  = Notice
        fields = ['id', 'title', 'body', 'category',
                  'created_by_name', 'is_active', 'published_at']


class GradeSubmitSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    marks         = serializers.DecimalField(max_digits=5, decimal_places=2,
                                             min_value=0, max_value=100)