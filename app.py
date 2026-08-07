"""
app.py
-------
Student Management System
Final Year Project

Problem Definition:
    Existing student record management is mostly manual, making it
    difficult to store, update and retrieve student information
    efficiently. This project develops a digital system to manage
    student records accurately.

Objectives implemented:
    - Maintain student records         -> Dashboard, Students list
    - Add, update and delete details   -> Full CRUD for Students & Courses
    - Search student information       -> Search box on Students/Courses
    - Generate reports                 -> Dashboard stats, Enrollment reports
    - Course enrollment                -> Enroll students into one or more courses
    - Admin login                      -> Session-based authentication

Tech stack: Python (Flask), HTML, CSS, JavaScript, Bootstrap, MySQL/SQLite
"""

import math
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

import database
import reports

# NOTE: template_folder="." because this project's HTML files live in the
# same folder as app.py (a flat layout), rather than in a separate
# "templates/" subfolder. This happens automatically if you upload files
# to GitHub from a mobile browser, which cannot preserve folder structure.
app = Flask(__name__, template_folder=".")
app.secret_key = "change-this-secret-key-in-production"


@app.route("/style.css")
def stylesheet():
    """Serve the CSS file, which also lives at the project root."""
    return send_from_directory(app.root_path, "style.css", mimetype="text/css")

PAGE_SIZE = 10


# ---------------------------------------------------------------------------
# Startup: create tables + a default admin user
# ---------------------------------------------------------------------------

def ensure_default_admin():
    conn = database.get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@sms.local",)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Admin User", "admin@sms.local", generate_password_hash("admin123")),
        )
        conn.commit()
    conn.close()


database.init_db()
ensure_default_admin()


@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard") if session.get("user_id") else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = database.get_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    conn = database.get_connection()

    total_students = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    total_courses = conn.execute("SELECT COUNT(*) c FROM courses").fetchone()["c"]

    top_course_row = conn.execute("""
        SELECT c.course_name, COUNT(e.id) cnt
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        GROUP BY e.course_id
        ORDER BY cnt DESC
        LIMIT 1
    """).fetchone()
    top_course = top_course_row["course_name"] if top_course_row else None

    month_prefix = datetime.now().strftime("%Y-%m")
    enrolled_this_month = conn.execute(
        "SELECT COUNT(DISTINCT student_id) c FROM enrollments WHERE enrolled_at LIKE ?",
        (f"{month_prefix}%",),
    ).fetchone()["c"]

    recent_students = conn.execute(
        "SELECT * FROM students ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        total_students=total_students,
        total_courses=total_courses,
        top_course=top_course,
        enrolled_this_month=enrolled_this_month,
        recent_students=recent_students,
    )


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

@app.route("/students")
@login_required
def students():
    query = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)

    conn = database.get_connection()
    if query:
        like = f"%{query}%"
        count_row = conn.execute(
            """SELECT COUNT(*) c FROM students
               WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ?""",
            (like, like, like),
        ).fetchone()
        total = count_row["c"]
        rows = conn.execute(
            """SELECT * FROM students
               WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ?
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (like, like, like, PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
        rows = conn.execute(
            "SELECT * FROM students ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()
    conn.close()

    total_pages = max(math.ceil(total / PAGE_SIZE), 1)

    return render_template(
        "students.html",
        active_page="students",
        students=rows,
        query=query,
        page=page,
        total_pages=total_pages,
    )


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "address": request.form.get("address", "").strip(),
        }
        if not data["first_name"] or not data["last_name"] or not data["email"]:
            flash("First name, last name and email are required.", "danger")
            return render_template("add_student.html", active_page="students", form_data=data)

        conn = database.get_connection()
        try:
            conn.execute(
                """INSERT INTO students (first_name, last_name, email, phone, address)
                   VALUES (?, ?, ?, ?, ?)""",
                (data["first_name"], data["last_name"], data["email"], data["phone"], data["address"]),
            )
            conn.commit()
            flash(f"Student '{data['first_name']} {data['last_name']}' added successfully.", "success")
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            flash(f"A student with email '{data['email']}' already exists.", "danger")
            return render_template("add_student.html", active_page="students", form_data=data)
        finally:
            conn.close()

    return render_template("add_student.html", active_page="students", form_data=None)


@app.route("/students/<int:student_id>")
@login_required
def view_student(student_id):
    conn = database.get_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))
    return render_template("view_student.html", active_page="students", student=student)


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    conn = database.get_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()

    if student is None:
        conn.close()
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    if request.method == "POST":
        data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "address": request.form.get("address", "").strip(),
            "is_active": 1 if request.form.get("is_active") == "1" else 0,
        }
        if not data["first_name"] or not data["last_name"] or not data["email"]:
            flash("First name, last name and email are required.", "danger")
            conn.close()
            return render_template("edit_student.html", active_page="students", student=data | {"id": student_id})

        try:
            conn.execute(
                """UPDATE students SET first_name=?, last_name=?, email=?, phone=?,
                   address=?, is_active=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (data["first_name"], data["last_name"], data["email"], data["phone"],
                 data["address"], data["is_active"], student_id),
            )
            conn.commit()
            flash("Student updated successfully.", "success")
            return redirect(url_for("view_student", student_id=student_id))
        except sqlite3.IntegrityError:
            flash(f"A student with email '{data['email']}' already exists.", "danger")
            return render_template("edit_student.html", active_page="students", student=data | {"id": student_id})
        finally:
            conn.close()

    conn.close()
    return render_template("edit_student.html", active_page="students", student=student)


@app.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    conn = database.get_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if student:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        flash(f"Student '{student['first_name']} {student['last_name']}' deleted.", "success")
    conn.close()
    return redirect(url_for("students"))


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@app.route("/courses")
@login_required
def courses():
    query = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)

    conn = database.get_connection()
    if query:
        like = f"%{query}%"
        total = conn.execute(
            "SELECT COUNT(*) c FROM courses WHERE course_name LIKE ? OR course_code LIKE ?",
            (like, like),
        ).fetchone()["c"]
        rows = conn.execute(
            """SELECT * FROM courses WHERE course_name LIKE ? OR course_code LIKE ?
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (like, like, PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) c FROM courses").fetchone()["c"]
        rows = conn.execute(
            "SELECT * FROM courses ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()
    conn.close()

    total_pages = max(math.ceil(total / PAGE_SIZE), 1)

    return render_template(
        "courses.html",
        active_page="courses",
        courses=rows,
        query=query,
        page=page,
        total_pages=total_pages,
    )


@app.route("/courses/add", methods=["GET", "POST"])
@login_required
def add_course():
    if request.method == "POST":
        data = {
            "course_name": request.form.get("course_name", "").strip(),
            "course_code": request.form.get("course_code", "").strip(),
            "duration": request.form.get("duration", "").strip(),
            "fee": request.form.get("fee", "0").strip(),
            "description": request.form.get("description", "").strip(),
        }
        if not data["course_name"] or not data["course_code"]:
            flash("Course name and course code are required.", "danger")
            return render_template("add_course.html", active_page="courses", form_data=data)

        try:
            fee_value = float(data["fee"] or 0)
        except ValueError:
            fee_value = 0.0

        conn = database.get_connection()
        try:
            conn.execute(
                """INSERT INTO courses (course_name, course_code, duration, fee, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (data["course_name"], data["course_code"], data["duration"], fee_value, data["description"]),
            )
            conn.commit()
            flash(f"Course '{data['course_name']}' added successfully.", "success")
            return redirect(url_for("courses"))
        except sqlite3.IntegrityError:
            flash(f"A course with code '{data['course_code']}' already exists.", "danger")
            return render_template("add_course.html", active_page="courses", form_data=data)
        finally:
            conn.close()

    return render_template("add_course.html", active_page="courses", form_data=None)


@app.route("/courses/<int:course_id>")
@login_required
def view_course(course_id):
    conn = database.get_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    enrolled_count = conn.execute(
        "SELECT COUNT(*) c FROM enrollments WHERE course_id = ?", (course_id,)
    ).fetchone()["c"]
    conn.close()
    if course is None:
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))
    return render_template("view_course.html", active_page="courses", course=course, enrolled_count=enrolled_count)


@app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_id):
    conn = database.get_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()

    if course is None:
        conn.close()
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))

    if request.method == "POST":
        data = {
            "course_name": request.form.get("course_name", "").strip(),
            "course_code": request.form.get("course_code", "").strip(),
            "duration": request.form.get("duration", "").strip(),
            "fee": request.form.get("fee", "0").strip(),
            "description": request.form.get("description", "").strip(),
            "is_active": 1 if request.form.get("is_active") == "1" else 0,
        }
        if not data["course_name"] or not data["course_code"]:
            flash("Course name and course code are required.", "danger")
            conn.close()
            return render_template("edit_course.html", active_page="courses", course=data | {"id": course_id})

        try:
            fee_value = float(data["fee"] or 0)
        except ValueError:
            fee_value = 0.0

        try:
            conn.execute(
                """UPDATE courses SET course_name=?, course_code=?, duration=?, fee=?,
                   description=?, is_active=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (data["course_name"], data["course_code"], data["duration"], fee_value,
                 data["description"], data["is_active"], course_id),
            )
            conn.commit()
            flash("Course updated successfully.", "success")
            return redirect(url_for("view_course", course_id=course_id))
        except sqlite3.IntegrityError:
            flash(f"A course with code '{data['course_code']}' already exists.", "danger")
            return render_template("edit_course.html", active_page="courses", course=data | {"id": course_id})
        finally:
            conn.close()

    conn.close()
    return render_template("edit_course.html", active_page="courses", course=course)


@app.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    conn = database.get_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if course:
        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        flash(f"Course '{course['course_name']}' deleted.", "success")
    conn.close()
    return redirect(url_for("courses"))


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

@app.route("/enroll-course", methods=["GET", "POST"])
@login_required
def enroll_course():
    conn = database.get_connection()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        course_ids = request.form.getlist("course_ids")

        if not student_id or not course_ids:
            flash("Please select a student and at least one course.", "danger")
            conn.close()
            return redirect(url_for("enroll_course"))

        added = 0
        for course_id in course_ids:
            try:
                conn.execute(
                    "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
                    (student_id, course_id),
                )
                added += 1
            except sqlite3.IntegrityError:
                pass  # already enrolled in this course -- skip silently
        conn.commit()
        conn.close()

        if added:
            flash(f"Enrolled student in {added} course(s) successfully.", "success")
        else:
            flash("Student was already enrolled in all selected courses.", "warning")
        return redirect(url_for("enrolled_students"))

    students_list = conn.execute(
        "SELECT * FROM students WHERE is_active = 1 ORDER BY first_name"
    ).fetchall()
    courses_list = conn.execute(
        "SELECT * FROM courses WHERE is_active = 1 ORDER BY course_name"
    ).fetchall()
    conn.close()

    return render_template(
        "enroll_course.html",
        active_page="enroll",
        students=students_list,
        courses=courses_list,
    )


@app.route("/enrolled-students")
@login_required
def enrolled_students():
    conn = database.get_connection()
    rows = conn.execute("""
        SELECT s.id, s.first_name, s.last_name, s.email,
               COUNT(e.id) AS course_count,
               COALESCE(SUM(c.fee), 0) AS total_fee
        FROM students s
        JOIN enrollments e ON e.student_id = s.id
        JOIN courses c ON c.id = e.course_id
        GROUP BY s.id
        ORDER BY s.first_name
    """).fetchall()
    conn.close()
    return render_template("enrolled_students.html", active_page="enrolled", enrolled=rows)


@app.route("/enrollment-details/<int:student_id>")
@login_required
def enrollment_details(student_id):
    conn = database.get_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if student is None:
        conn.close()
        flash("Student not found.", "danger")
        return redirect(url_for("enrolled_students"))

    enrollments = conn.execute("""
        SELECT e.id AS enrollment_id, c.course_name, c.description, c.fee
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        WHERE e.student_id = ?
        ORDER BY c.course_name
    """, (student_id,)).fetchall()
    conn.close()

    total_fee = sum(e["fee"] for e in enrollments)

    return render_template(
        "enrollment_details.html",
        active_page="enrolled",
        student=student,
        enrollments=enrollments,
        total_fee=total_fee,
    )


@app.route("/enrollments/<int:enrollment_id>/delete", methods=["POST"])
@login_required
def unenroll(enrollment_id):
    conn = database.get_connection()
    enrollment = conn.execute("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,)).fetchone()
    student_id = enrollment["student_id"] if enrollment else None
    if enrollment:
        conn.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
        conn.commit()
        flash("Enrollment removed.", "success")
    conn.close()
    return redirect(url_for("enrollment_details", student_id=student_id) if student_id else url_for("enrolled_students"))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.route("/reports")
@login_required
def reports_page():
    conn = database.get_connection()
    student_count = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    course_count = conn.execute("SELECT COUNT(*) c FROM courses").fetchone()["c"]
    conn.close()
    return render_template(
        "reports.html",
        active_page="reports",
        student_count=student_count,
        course_count=course_count,
    )


@app.route("/reports/<kind>/pdf")
@login_required
def report_pdf(kind):
    if kind not in ("students", "courses"):
        flash("Invalid report type.", "danger")
        return redirect(url_for("reports_page"))

    conn = database.get_connection()
    items = conn.execute(f"SELECT * FROM {kind}").fetchall()
    conn.close()

    title = "Student Management System - Students Report" if kind == "students" else "Student Management System - Courses Report"
    pdf_file = reports.generate_pdf(items, kind=kind, title=title)
    return send_file(pdf_file, mimetype="application/pdf", as_attachment=True, download_name=f"{kind}_report.pdf")


@app.route("/reports/<kind>/csv")
@login_required
def report_csv(kind):
    if kind not in ("students", "courses"):
        flash("Invalid report type.", "danger")
        return redirect(url_for("reports_page"))

    conn = database.get_connection()
    items = conn.execute(f"SELECT * FROM {kind}").fetchall()
    conn.close()

    csv_file = reports.generate_csv(items, kind=kind)
    return send_file(csv_file, mimetype="text/csv", as_attachment=True, download_name=f"{kind}_report.csv")


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
