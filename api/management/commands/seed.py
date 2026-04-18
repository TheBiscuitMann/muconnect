from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Department, Student, Faculty, Course, Enrollment, Result

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        cse, _ = Department.objects.get_or_create(
            short_code='CSE',
            defaults={
                'name':   'Computer Science & Engineering',
                'school': 'Science & Technology',
            }
        )

        # ── ADMIN ────────────────────────────────────────────────
        admin_user, _ = User.objects.get_or_create(
            email='admin@metrouni.edu.bd',
            defaults={
                'username':   'admin',
                'first_name': 'Admin',
                'last_name':  'MU',
                'role':       'admin',
                'is_staff':   True,
            }
        )
        admin_user.set_password('password')
        admin_user.save()

        # ── FACULTY 1 — Abdul Wadud Shakib ───────────────────────
        fac1_user, _ = User.objects.get_or_create(
            email='shakib@metrouni.edu.bd',
            defaults={
                'username':   'shakib',
                'first_name': 'Abdul Wadud',
                'last_name':  'Shakib',
                'role':       'faculty',
            }
        )
        fac1_user.set_password('password')
        fac1_user.save()

        faculty1, _ = Faculty.objects.get_or_create(
            user=fac1_user,
            defaults={
                'faculty_id':     'FAC-001',
                'department':     cse,
                'designation':    'Lecturer',
                'specialization': 'Web Development & Software Engineering',
            }
        )
        # Force update in case faculty already exists
        Faculty.objects.filter(user=fac1_user).update(
            faculty_id='FAC-001', designation='Lecturer',
            specialization='Web Development & Software Engineering'
        )

        # ── FACULTY 2 — Rishad Amin Pulok ────────────────────────
        fac2_user, _ = User.objects.get_or_create(
            email='pulok@metrouni.edu.bd',
            defaults={
                'username':   'pulok',
                'first_name': 'Rishad Amin',
                'last_name':  'Pulok',
                'role':       'faculty',
            }
        )
        fac2_user.set_password('password')
        fac2_user.save()

        faculty2, created = Faculty.objects.get_or_create(
            user=fac2_user,
            defaults={
                'faculty_id':     'FAC-002',
                'department':     cse,
                'designation':    'Lecturer',
                'specialization': 'Algorithms & Artificial Intelligence',
            }
        )
        Faculty.objects.filter(user=fac2_user).update(
            faculty_id='FAC-002', designation='Lecturer',
            specialization='Algorithms & Artificial Intelligence'
        )

        self.stdout.write('  ✓ Faculty created/updated')

        # ── COURSES ───────────────────────────────────────────────
        # Shakib → 4 courses (Semesters 1–4)
        # Pulok  → 4 courses (Semesters 5–8)
        # Others → no faculty assigned (future assignment)

        courses_raw = [
            # (code, title, credit, semester, faculty_obj or None)

            # ── Shakib's 4 courses ──
            ('CSE101', 'Introduction to Programming',  3, 1, faculty1),
            ('CSE201', 'Data Structures',              3, 2, faculty1),
            ('CSE301', 'Database Systems',             3, 3, faculty1),
            ('CSE401', 'Software Engineering',         3, 4, faculty1),

            # ── Pulok's 4 courses ──
            ('CSE501', 'Algorithms & Complexity',      3, 5, faculty2),
            ('CSE601', 'Artificial Intelligence',      3, 6, faculty2),
            ('CSE701', 'Machine Learning',             3, 7, faculty2),
            ('CSE801', 'Deep Learning',                3, 8, faculty2),

            # ── Unassigned courses ──
            ('CSE102', 'Discrete Mathematics',         3, 1, None),
            ('CSE103', 'Digital Logic Design',         3, 1, None),
            ('CSE202', 'Object Oriented Programming',  3, 2, None),
            ('CSE203', 'Computer Architecture',        3, 2, None),
            ('CSE302', 'Algorithm Design',             3, 3, None),
            ('CSE303', 'Computer Networks',            3, 3, None),
            ('CSE402', 'Operating Systems',            3, 4, None),
            ('CSE403', 'Computer Graphics',            3, 4, None),
            ('CSE502', 'Web Technologies',             3, 5, None),
            ('CSE503', 'Mobile App Development',       3, 5, None),
            ('CSE602', 'Cybersecurity Fundamentals',   3, 6, None),
            ('CSE603', 'Cloud Computing',              3, 6, None),
            ('CSE702', 'Natural Language Processing',  3, 7, None),
            ('CSE703', 'Distributed Systems',          3, 7, None),
            ('CSE802', 'Blockchain Technology',        3, 8, None),
            ('CSE803', 'IoT Systems',                  3, 8, None),
            ('CSE901', 'Research Methodology',         3, 9, None),
            ('CSE902', 'Software Project Management',  3, 9, None),
            ('CSE903', 'Entrepreneurship in Tech',     3, 9, None),
            ('CSE1001','Thesis / Project Part I',      6, 10, None),
            ('CSE1002','Advanced Topics in AI',        3, 10, None),
            ('CSE1003','Tech Ethics & Policy',         3, 10, None),
        ]

        courses = {}
        for code, title, credit, sem, fac in courses_raw:
            c, _ = Course.objects.get_or_create(
                code=code,
                defaults={
                    'title':      title,
                    'credit':     credit,
                    'semester':   sem,
                    'department': cse,
                    'faculty':    fac,
                }
            )
            # Always update faculty assignment to ensure correct state
            Course.objects.filter(code=code).update(faculty=fac)
            courses[code] = Course.objects.get(code=code)

        self.stdout.write(f'  ✓ {len(courses)} courses created/updated')
        self.stdout.write('  ✓ Shakib assigned: CSE101, CSE201, CSE301, CSE401')
        self.stdout.write('  ✓ Pulok  assigned: CSE501, CSE601, CSE701, CSE801')

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

        sem_to_codes = {}
        for code, title, credit, sem, fac in courses_raw:
            sem_to_codes.setdefault(sem, []).append(code)

        # ── HELPER: create student + results ─────────────────────
        def create_student(first, last, email, username, student_id,
                           marks_by_sem, completed_sems, current_sem,
                           ungraded_sem=None):
            """
            ungraded_sem: if set, enrollments for that semester are created
            but NO results are submitted (faculty needs to grade them).
            """
            u, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    'username':   username,
                    'first_name': first,
                    'last_name':  last,
                    'role':       'student',
                }
            )
            u.set_password('password')
            u.save()

            s, _ = Student.objects.get_or_create(
                user=u,
                defaults={
                    'student_id':       student_id,
                    'department':       cse,
                    'batch':            2023,
                    'current_semester': current_sem,
                    'cgpa':             0,
                }
            )
            Student.objects.filter(user=u).update(
                student_id=student_id,
                batch=2023,
                current_semester=current_sem,
            )
            s.refresh_from_db()

            total_points  = 0.0
            total_credits = 0

            for sem_num in range(1, completed_sems + 1):
                sem_label, sem_year = sem_labels[sem_num]
                sem_courses = sem_to_codes.get(sem_num, [])
                marks_list  = marks_by_sem.get(sem_num, [80] * len(sem_courses))

                for i, code in enumerate(sem_courses):
                    course = courses[code]
                    marks  = marks_list[i] if i < len(marks_list) else 80

                    enrollment, _ = Enrollment.objects.get_or_create(
                        student=s, course=course,
                        defaults={'semester': sem_label, 'year': sem_year}
                    )

                    # Skip grading for ungraded_sem
                    if ungraded_sem and sem_num == ungraded_sem:
                        continue

                    g = Result.calculate_grade(marks)
                    Result.objects.get_or_create(
                        enrollment=enrollment,
                        defaults={
                            **g,
                            'marks':        marks,
                            'published':    True,
                            'submitted_by': fac1_user,
                            'published_by': admin_user,
                        }
                    )
                    total_points  += float(g['grade_point']) * course.credit
                    total_credits += course.credit

            cgpa = round(total_points / total_credits, 2) if total_credits else 0.0
            Student.objects.filter(user=u).update(cgpa=cgpa)
            self.stdout.write(
                f'  ✓ {first} {last} | {student_id} | CGPA: {cgpa}'
                + (f' | Sem {ungraded_sem} LEFT UNGRADED' if ungraded_sem else '')
            )

        # ── STUDENT 1 — Rafiqul Alam ──────────────────────────────
        # Semesters 1–3 graded, Semester 4 LEFT UNGRADED
        # → Shakib can log in and grade Semester 4 (CSE401 / Software Eng)
        # → He can give Rafiqul a failing mark to test the retake flow
        create_student(
            first='Rafiqul', last='Alam',
            email='rafiq@student.metrouni.edu.bd',
            username='rafiq',
            student_id='231-115-100',
            marks_by_sem={
                1: [85, 78, 91],
                2: [72, 88, 65],
                3: [88, 76, 79],
                4: [92, 83, 70],   # marks provided but sem 4 won't be graded
            },
            completed_sems=4,
            current_sem=4,
            ungraded_sem=4,        # ← leave sem 4 ungraded
        )

        # ── STUDENT 2 — Mosaddeq Hussain ─────────────────────────
        # All 9 semesters graded, CGPA ~3.98
        create_student(
            first='Mosaddeq', last='Hussain',
            email='mosaddeq@student.metrouni.edu.bd',
            username='mosaddeq',
            student_id='231-115-253',
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
        # All 9 semesters graded, CGPA ~3.78
        create_student(
            first='Fariha', last='Rahman',
            email='fariha@student.metrouni.edu.bd',
            username='fariha',
            student_id='231-115-102',
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

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  admin@metrouni.edu.bd          / password  (Admin)')
        self.stdout.write('  shakib@metrouni.edu.bd         / password  (FAC-001 — Shakib)')
        self.stdout.write('  pulok@metrouni.edu.bd          / password  (FAC-002 — Pulok)')
        self.stdout.write('  rafiq@student.metrouni.edu.bd  / password  (Rafiqul — Sem 4 UNGRADED)')
        self.stdout.write('  mosaddeq@student.metrouni.edu.bd / password  (Mosaddeq)')
        self.stdout.write('  fariha@student.metrouni.edu.bd / password  (Fariha)')
        self.stdout.write('\nTest the retake flow:')
        self.stdout.write('  1. Login as Shakib → My Courses → CSE401 (Software Engineering)')
        self.stdout.write('  2. Enter marks for Rafiqul — give him < 45 to trigger F grade')
        self.stdout.write('  3. Submit grades → Admin publishes them')
        self.stdout.write('  4. Login as Rafiqul → My Results → Semester 4 → Apply for Retake')
        self.stdout.write('  5. Login as Shakib → Retake Applications → Approve or Reject')