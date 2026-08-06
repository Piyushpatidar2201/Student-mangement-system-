"""
seed_data.py
-------------
Populates the database with sample students, courses, and a few
enrollments so the app has data to demo immediately.

Run with:  python seed_data.py
"""

import database

STUDENTS = [
    ("John", "Doe", "john.doe@example.com", "+91 98765 43210", "Indore, MP", 1),
    ("Jane", "Smith", "jane.smith@example.com", "+91 98123 45678", "Bhopal, MP", 1),
    ("Mike", "Johnson", "mike.j@example.com", "+91 91234 56789", "Ujjain, MP", 1),
    ("Alex", "Johnson", "alex.johnson@example.com", "+91 90000 11122", "Dewas, MP", 1),
    ("Priya", "Sharma", "priya.sharma@example.com", "+91 99887 76655", "Indore, MP", 1),
]

COURSES = [
    ("Introduction to Computer Science", "CS101", "4 Months", 3999.00,
     "A fundamental course covering algorithms, data structures, and computer architecture."),
    ("Web Development Bootcamp", "WEB101", "6 Months", 7999.00,
     "Build responsive websites and apps using HTML, CSS, JavaScript and Flask."),
    ("Data Structures & Algorithms", "DSA201", "5 Months", 5999.00,
     "Learn efficient data handling, sorting, searching, and problem solving."),
    ("Cloud Computing Essentials", "CLD301", "3 Months", 4500.00,
     "Infrastructure, services, and deployment models across major cloud providers."),
]

# (student_email, course_code) pairs
ENROLLMENTS = [
    ("john.doe@example.com", "CS101"),
    ("john.doe@example.com", "WEB101"),
    ("jane.smith@example.com", "DSA201"),
    ("mike.j@example.com", "CS101"),
    ("alex.johnson@example.com", "WEB101"),
    ("alex.johnson@example.com", "DSA201"),
    ("alex.johnson@example.com", "CLD301"),
]


def seed():
    database.init_db()
    conn = database.get_connection()
    cur = conn.cursor()

    added_students = 0
    for s in STUDENTS:
        try:
            cur.execute(
                "INSERT INTO students (first_name, last_name, email, phone, address, is_active) VALUES (?,?,?,?,?,?)",
                s,
            )
            added_students += 1
        except Exception:
            pass

    added_courses = 0
    for c in COURSES:
        try:
            cur.execute(
                "INSERT INTO courses (course_name, course_code, duration, fee, description) VALUES (?,?,?,?,?)",
                c,
            )
            added_courses += 1
        except Exception:
            pass

    conn.commit()

    added_enrollments = 0
    for email, code in ENROLLMENTS:
        student = cur.execute("SELECT id FROM students WHERE email = ?", (email,)).fetchone()
        course = cur.execute("SELECT id FROM courses WHERE course_code = ?", (code,)).fetchone()
        if student and course:
            try:
                cur.execute(
                    "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
                    (student["id"], course["id"]),
                )
                added_enrollments += 1
            except Exception:
                pass

    conn.commit()
    conn.close()

    print(f"Seeded {added_students} student(s), {added_courses} course(s), {added_enrollments} enrollment(s).")


if __name__ == "__main__":
    seed()
