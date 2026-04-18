from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin',   'Admin'),
    ]
    role  = models.CharField(max_length=10, choices=ROLES, default='student')
    email = models.EmailField(unique=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class Department(models.Model):
    name       = models.CharField(max_length=100)
    school     = models.CharField(max_length=100)
    short_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Student(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    student_id       = models.CharField(max_length=20, unique=True)
    department       = models.ForeignKey(Department, on_delete=models.PROTECT)
    batch            = models.IntegerField()
    current_semester = models.IntegerField(default=1)
    cgpa             = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    phone            = models.CharField(max_length=15, blank=True)

    # ── Peer Network ──────────────────────────────────────────
    is_mentor        = models.BooleanField(default=False)
    mentor_bio       = models.TextField(blank=True, help_text="Short bio shown on mentor profile")
    mentor_since     = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.student_id}"


class Faculty(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty')
    faculty_id     = models.CharField(max_length=20, unique=True)
    department     = models.ForeignKey(Department, on_delete=models.PROTECT)
    designation    = models.CharField(max_length=50)
    specialization = models.CharField(max_length=100, blank=True)
    phone          = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.designation}"

    class Meta:
        verbose_name_plural = 'Faculty'


class Course(models.Model):
    code       = models.CharField(max_length=10, unique=True)
    title      = models.CharField(max_length=100)
    credit     = models.IntegerField()
    semester   = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    faculty    = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.code} — {self.title}"


class Enrollment(models.Model):
    student  = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course   = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)
    year     = models.IntegerField()

    class Meta:
        unique_together = ('student', 'course', 'semester')

    def __str__(self):
        return f"{self.student.student_id} — {self.course.code} ({self.semester})"


class Result(models.Model):
    enrollment   = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='result')
    marks        = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade        = models.CharField(max_length=4, blank=True)
    grade_point  = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    published    = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_results')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_results')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    @staticmethod
    def calculate_grade(marks: float) -> dict:
        if   marks >= 80: return {'grade': 'A',  'grade_point': 4.00}
        elif marks >= 75: return {'grade': 'A-', 'grade_point': 3.75}
        elif marks >= 70: return {'grade': 'B+', 'grade_point': 3.50}
        elif marks >= 65: return {'grade': 'B',  'grade_point': 3.25}
        elif marks >= 60: return {'grade': 'B-', 'grade_point': 3.00}
        elif marks >= 55: return {'grade': 'C+', 'grade_point': 2.75}
        elif marks >= 50: return {'grade': 'C',  'grade_point': 2.50}
        elif marks >= 45: return {'grade': 'D',  'grade_point': 2.25}
        else:             return {'grade': 'F',  'grade_point': 0.00}

    def __str__(self):
        return f"{self.enrollment} — {self.grade or 'Not graded'}"


class Notice(models.Model):
    CATEGORIES = [
        ('exam',     'Exam'),
        ('academic', 'Academic'),
        ('event',    'Event'),
        ('general',  'General'),
    ]
    title        = models.CharField(max_length=200)
    body         = models.TextField()
    category     = models.CharField(max_length=10, choices=CATEGORIES, default='general')
    created_by   = models.ForeignKey(User, on_delete=models.PROTECT)
    is_active    = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title


# ══════════════════════════════════════════════════════════════════
# Peer Network Feature
# ══════════════════════════════════════════════════════════════════

class Conversation(models.Model):
    """A chat between a mentor (student) and a mentee (student)."""
    mentor     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mentor_conversations')
    mentee     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mentee_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('mentor', 'mentee')
        ordering        = ['-updated_at']

    def __str__(self):
        return f"{self.mentee.user.get_full_name()} ↔ {self.mentor.user.get_full_name()}"


class Message(models.Model):
    """A single message inside a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(Student, on_delete=models.CASCADE)
    text         = models.TextField()
    created_at   = models.DateTimeField(auto_now_add=True)
    read_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.user.first_name}: {self.text[:30]}"

class RetakeApplication(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    TYPE_CHOICES = [
        ('retake',         'Retake Exam'),
        ('supplementary',  'Supplementary Exam'),
    ]

    student    = models.ForeignKey(Student,    on_delete=models.CASCADE, related_name='retake_applications')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='retake_applications')
    exam_type  = models.CharField(max_length=20, choices=TYPE_CHOICES, default='retake')
    reason     = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'enrollment', 'exam_type')
        ordering        = ['-applied_at']

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.enrollment.course.code} ({self.exam_type})"

# ══════════════════════════════════════════════════════════════════
# Attendance Feature
# ══════════════════════════════════════════════════════════════════

class AttendanceSession(models.Model):
    """One class session for a course on a specific date."""
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    batch      = models.CharField(max_length=20)   # e.g. 'CSE 58(C+G)'
    date       = models.DateField()
    topic      = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'batch', 'date')
        ordering        = ['-date']

    def __str__(self):
        return f"{self.course.code} | {self.batch} | {self.date}"


class AttendanceRecord(models.Model):
    """Whether a student was present or absent in a session."""
    session   = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    present   = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        status = 'Present' if self.present else 'Absent'
        return f"{self.student.student_id} | {self.session} | {status}"