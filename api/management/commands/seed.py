from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Department, Student, Faculty, Course, Enrollment, Result

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding...')

        cse, _ = Department.objects.get_or_create(
            short_code='CSE',
            defaults={'name': 'Computer Science & Engineering', 'school': 'Science & Technology'}
        )

        admin, _ = User.objects.get_or_create(
            email='admin@metrouni.edu.bd',
            defaults={'username': 'admin', 'first_name': 'Admin',
                      'last_name': 'MU', 'role': 'admin', 'is_staff': True}
        )
        admin.set_password('password')
        admin.save()

        fac_user, _ = User.objects.get_or_create(
            email='shakib@metrouni.edu.bd',
            defaults={'username': 'shakib', 'first_name': 'Abdul Wadud',
                      'last_name': 'Shakib', 'role': 'faculty'}
        )
        fac_user.set_password('password')
        fac_user.save()

        faculty, _ = Faculty.objects.get_or_create(
            user=fac_user,
            defaults={'faculty_id': 'FAC-001', 'department': cse,
                      'designation': 'Lecturer', 'specialization': 'Web Development'}
        )

        stu_user, _ = User.objects.get_or_create(
            email='rafiq@student.metrouni.edu.bd',
            defaults={'username': 'rafiq', 'first_name': 'Rafiqul',
                      'last_name': 'Alam', 'role': 'student'}
        )
        stu_user.set_password('password')
        stu_user.save()

        student, _ = Student.objects.get_or_create(
            user=stu_user,
            defaults={'student_id': '2022010045', 'department': cse,
                      'batch': 2022, 'current_semester': 6}
        )

        db_c,  _ = Course.objects.get_or_create(code='CSE301', defaults={'title': 'Database Systems',    'credit': 3, 'semester': 5, 'department': cse, 'faculty': faculty})
        se_c,  _ = Course.objects.get_or_create(code='CSE303', defaults={'title': 'Software Engineering', 'credit': 3, 'semester': 5, 'department': cse, 'faculty': faculty})
        net_c, _ = Course.objects.get_or_create(code='CSE305', defaults={'title': 'Computer Networks',   'credit': 3, 'semester': 5, 'department': cse, 'faculty': faculty})

        for course, marks in [(db_c, 88), (se_c, 79), (net_c, 83)]:
            enrollment, _ = Enrollment.objects.get_or_create(
                student=student, course=course,
                defaults={'semester': 'Autumn 2025', 'year': 2025}
            )
            g = Result.calculate_grade(marks)
            Result.objects.get_or_create(
                enrollment=enrollment,
                defaults={**g, 'marks': marks, 'published': True,
                          'submitted_by': fac_user, 'published_by': admin}
            )

        student.cgpa = 3.75
        student.save()

        self.stdout.write(self.style.SUCCESS('Done! Test accounts:'))
        self.stdout.write('  Admin:   admin@metrouni.edu.bd / password')
        self.stdout.write('  Faculty: shakib@metrouni.edu.bd / password')
        self.stdout.write('  Student: rafiq@student.metrouni.edu.bd / password')