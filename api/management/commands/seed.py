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

        # ── ADMIN ────────────────────────────────────────────────
        admin, _ = User.objects.get_or_create(
            email='admin@metrouni.edu.bd',
            defaults={'username': 'admin', 'first_name': 'Admin', 'last_name': 'MU', 'role': 'admin', 'is_staff': True}
        )
        admin.set_password('password')
        admin.save()

        # ── FACULTY ──────────────────────────────────────────────
        fac_user, _ = User.objects.get_or_create(
            email='shakib@metrouni.edu.bd',
            defaults={'username': 'shakib', 'first_name': 'Abdul Wadud', 'last_name': 'Shakib', 'role': 'faculty'}
        )
        fac_user.set_password('password')
        fac_user.save()

        faculty, _ = Faculty.objects.get_or_create(
            user=fac_user,
            defaults={'faculty_id': 'FAC-001', 'department': cse, 'designation': 'Lecturer', 'specialization': 'Web Development'}
        )

        # ── COURSES (12 semesters worth) ─────────────────────────
        courses_data = [
            # Sem 1 — Spring 2023
            ('CSE101', 'Introduction to Programming',   3, 1),
            ('CSE102', 'Discrete Mathematics',          3, 1),
            ('CSE103', 'Digital Logic Design',          3, 1),
            # Sem 2 — Summer 2023
            ('CSE201', 'Data Structures',               3, 2),
            ('CSE202', 'Object Oriented Programming',   3, 2),
            ('CSE203', 'Computer Architecture',         3, 2),
            # Sem 3 — Autumn 2023
            ('CSE301', 'Database Systems',              3, 3),
            ('CSE302', 'Algorithm Design',              3, 3),
            ('CSE303', 'Software Engineering',          3, 3),
            # Sem 4 — Spring 2024
            ('CSE401', 'Computer Networks',             3, 4),
            ('CSE402', 'Operating Systems',             3, 4),
            ('CSE403', 'Artificial Intelligence',       3, 4),
            # Sem 5 — Summer 2024
            ('CSE501', 'Web Technologies',              3, 5),
            ('CSE502', 'Mobile App Development',        3, 5),
            ('CSE503', 'Machine Learning',              3, 5),
            # Sem 6 — Autumn 2024
            ('CSE601', 'Cybersecurity Fundamentals',    3, 6),
            ('CSE602', 'Cloud Computing',               3, 6),
            ('CSE603', 'Compiler Design',               3, 6),
            # Sem 7 — Spring 2025
            ('CSE701', 'Computer Graphics',             3, 7),
            ('CSE702', 'Natural Language Processing',   3, 7),
            ('CSE703', 'Distributed Systems',           3, 7),
            # Sem 8 — Summer 2025
            ('CSE801', 'Deep Learning',                 3, 8),
            ('CSE802', 'Blockchain Technology',         3, 8),
            ('CSE803', 'IoT Systems',                   3, 8),
            # Sem 9 — Autumn 2025
            ('CSE901', 'Research Methodology',          3, 9),
            ('CSE902', 'Software Project Management',   3, 9),
            ('CSE903', 'Entrepreneurship in Tech',      3, 9),
            # Sem 10 — Spring 2026 (current)
            ('CSE1001', 'Thesis / Project Part I',      6, 10),
            ('CSE1002', 'Advanced Topics in AI',        3, 10),
            ('CSE1003', 'Tech Ethics & Policy',         3, 10),
        ]

        courses = {}
        for code, title, credit, sem in courses_data:
            c, _ = Course.objects.get_or_create(
                code=code,
                defaults={'title': title, 'credit': credit, 'semester': sem, 'department': cse, 'faculty': faculty}
            )
            courses[code] = c

        # ── SEMESTER LABELS ───────────────────────────────────────
        sem_labels = {
            1:  ('Spring 2023', 2023),
            2:  ('Summer 2023', 2023),
            3:  ('Autumn 2023', 2023),
            4:  ('Spring 2024', 2024),
            5:  ('Summer 2024', 2024),
            6:  ('Autumn 2024', 2024),
            7:  ('Spring 2025', 2025),
            8:  ('Summer 2025', 2025),
            9:  ('Autumn 2025', 2025),
            10: ('Spring 2026', 2026),
        }

        # ── HELPER: create student + results ─────────────────────
        def create_student(first, last, email, username, student_id, cgpa_display, marks_by_sem, completed_sems, current_sem):
            u, _ = User.objects.get_or_create(
                email=email,
                defaults={'username': username, 'first_name': first, 'last_name': last, 'role': 'student'}
            )
            u.set_password('password')
            u.save()

            s, _ = Student.objects.get_or_create(user=u, defaults={
                'student_id': student_id, 'department': cse,
                'batch': 2023, 'current_semester': current_sem, 'cgpa': 0,
            })
            Student.objects.filter(user=u).update(
                student_id=student_id, batch=2023,
                current_semester=current_sem,
            )
            s.refresh_from_db()

            total_points  = 0.0
            total_credits = 0

            for sem_num in range(1, completed_sems + 1):
                sem_label, sem_year = sem_labels[sem_num]
                sem_courses = [code for code, _, _, sn in courses_data if sn == sem_num]
                marks_list  = marks_by_sem.get(sem_num, [85, 80, 78])

                for i, code in enumerate(sem_courses):
                    course  = courses[code]
                    marks   = marks_list[i] if i < len(marks_list) else 80

                    enrollment, _ = Enrollment.objects.get_or_create(
                        student=s, course=course,
                        defaults={'semester': sem_label, 'year': sem_year}
                    )
                    g = Result.calculate_grade(marks)
                    Result.objects.get_or_create(
                        enrollment=enrollment,
                        defaults={**g, 'marks': marks, 'published': True,
                                  'submitted_by': fac_user, 'published_by': admin}
                    )
                    total_points  += float(g['grade_point']) * course.credit
                    total_credits += course.credit

            cgpa = round(total_points / total_credits, 2) if total_credits else 0.0
            Student.objects.filter(user=u).update(cgpa=cgpa)
            self.stdout.write(f'  ✓ {first} {last} | ID: {student_id} | CGPA: {cgpa}')

        # ── STUDENT 1 — Rafiqul Alam ──────────────────────────────
        # Admitted Spring 2023, completed 4 semesters (batch 2023, sem 4)
        create_student(
            first='Rafiqul', last='Alam',
            email='rafiq@student.metrouni.edu.bd',
            username='rafiq',
            student_id='231-115-100',
            cgpa_display='3.75',
            marks_by_sem={
                1: [85, 78, 91],
                2: [72, 88, 65],
                3: [88, 76, 79],
                4: [92, 83, 70],
            },
            completed_sems=4,
            current_sem=4,
        )

        # ── STUDENT 2 — Mosaddeq Hussain ─────────────────────────
        # Admitted Spring 2023, completed 9 semesters, currently in 10th
        # ID: 231-115-253, CGPA: 3.96
        create_student(
            first='Mosaddeq', last='Hussain',
            email='mosaddeq@student.metrouni.edu.bd',
            username='mosaddeq',
            student_id='231-115-253',
            cgpa_display='3.96',
            marks_by_sem={
    1:  [98, 97, 78],
    2:  [96, 98, 99],
    3:  [99, 97, 68],
    4:  [98, 99, 97],
    5:  [97, 99, 98],
    6:  [99, 98, 97],
    7:  [98, 97, 99],
    8:  [99, 98, 98],
    9:  [97, 99, 98],
},
            completed_sems=9,
            current_sem=10,
        )

        # ── STUDENT 3 — Fariha Rahman ─────────────────────────────
        # Admitted Spring 2023, completed 9 semesters, currently in 10th
        # ID: 231-115-102, CGPA: 3.78
        create_student(
            first='Fariha', last='Rahman',
            email='fariha@student.metrouni.edu.bd',
            username='fariha',
            student_id='231-115-102',
            cgpa_display='3.78',
            marks_by_sem={
    1:  [82, 78, 75],
    2:  [76, 80, 65],
    3:  [83, 77, 81],
    4:  [85, 80, 78],
    5:  [79, 83, 80],
    6:  [77, 81, 84],
    7:  [83, 79, 78],
    8:  [85, 82, 80],
    9:  [79, 83, 82],
},
            completed_sems=9,
            current_sem=10,
        )

        self.stdout.write(self.style.SUCCESS('\nAll students seeded successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:    admin@metrouni.edu.bd / password')
        self.stdout.write('  Faculty:  shakib@metrouni.edu.bd / password')
        self.stdout.write('  Rafiqul:  rafiq@student.metrouni.edu.bd / password')
        self.stdout.write('  Mosaddeq: mosaddeq@student.metrouni.edu.bd / password')
        self.stdout.write('  Fariha:   fariha@student.metrouni.edu.bd / password')