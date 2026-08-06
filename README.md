# Student Management System (Live Flask App)

Yeh project aapke uploaded template ka **exact same design** use karta hai, lekin ab
ek asli, live-running website hai — **Python (Flask)** backend ke saath, real
database (SQLite by default, MySQL-ready), login system, aur poora CRUD.

## Tech Stack (same jo form me fill ki thi)
- **Python (Flask)** — backend
- **HTML, CSS, JavaScript** — frontend
- **Bootstrap 5** — UI framework
- **MySQL / SQLite** — database

## Features
- **Login/Logout** — session-based admin authentication
- **Dashboard** — live stats: total students, total courses, top performing course, students enrolled this month, recent registrations
- **Students** — list (search + pagination), add, view, edit, delete
- **Courses** — list (search + pagination), add, view, edit, delete
- **Enroll to Course** — select a student + multiple courses, live fee summary (JavaScript), submit to enroll
- **Enrolled Students** — summary of every student's course count and total fee
- **Enrollment Details** — per-student breakdown with option to remove a course enrollment
- **404 / 500 error pages** — matching the same design

## Kaise Chalayein (How to Run)

1. Dependencies install karo:
   ```bash
   pip install -r requirements.txt
   ```

2. Sample data daalne ke liye (optional, demo ke liye achha hai):
   ```bash
   python seed_data.py
   ```

3. App run karo:
   ```bash
   python app.py
   ```

4. Browser me kholo: **http://127.0.0.1:5000**

5. Login karo:
   - **Email:** `admin@sms.local`
   - **Password:** `admin123`

Database file khud-ba-khud ban jaata hai `instance/sms.db` pe — koi manual setup nahi chahiye.

## Project Structure
```
sms_app/
├── app.py                    # Saari routes yahin hain
├── database.py                # DB connection + schema (SQLite, MySQL-ready)
├── seed_data.py                # Demo data daalne ke liye
├── requirements.txt
├── templates/
│   ├── base.html                 # Sidebar + navbar (sabhi pages isi se extend hoti hain)
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html / add_student.html / edit_student.html / view_student.html
│   ├── courses.html / add_course.html / edit_course.html / view_course.html
│   ├── enroll_course.html
│   ├── enrolled_students.html
│   ├── enrollment_details.html
│   ├── 404.html / 500.html
├── static/css/style.css       # Aapke original template ka wahi CSS
└── instance/sms.db            # Auto-created SQLite database
```

## MySQL Pe Switch Karna (jaisa form me likha tha)

Ye project by default SQLite pe chalta hai (zero setup), lekin MySQL pe switch karna easy hai:

1. `pip install pymysql`
2. MySQL me database banao:
   ```sql
   CREATE DATABASE student_management_system;
   ```
3. `database.py` file kholo — upar wala SQLite section comment karo, aur neeche wala MySQL section uncomment karo. Apna host/user/password `DB_CONFIG` me daal do.
4. App normal chalao — tables khud ban jayengi.

Koi aur file change nahi karni padegi — `app.py` sirf `database.get_connection()` use karta hai.

## Render.com Pe Deploy Karke Live Public Link Banana

Yeh project **deploy-ready** hai — `Procfile`, `render.yaml` aur `gunicorn` pehle se add hain.

### Step 1: GitHub pe code upload karo
1. [github.com](https://github.com) pe account banao (agar nahi hai)
2. Naya repository banao (e.g. `student-management-system`)
3. Is poore `sms_app` folder ka content us repo me upload karo:
   - GitHub website se **"uploading an existing file"** use kar sakte ho (drag & drop), ya
   - Terminal se:
     ```bash
     cd sms_app
     git init
     git add .
     git commit -m "Student Management System"
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/student-management-system.git
     git push -u origin main
     ```

### Step 2: Render pe deploy karo
1. [render.com](https://render.com) pe jao → **Sign up with GitHub**
2. Dashboard me **"New +"** → **"Web Service"** click karo
3. Apna GitHub repo select karo (`student-management-system`)
4. Settings automatically aa jayengi (`render.yaml` se), ya manually daalo:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
5. **"Create Web Service"** dabao
6. 2-3 minute me build ho jayega, aur ek link milega jaise:
   ```
   https://student-management-system-xxxx.onrender.com
   ```
7. Us link ko kholo — login: `admin@sms.local` / `admin123`

### Zaroori baat (Important Note)
Render ke **free tier** pe filesystem *ephemeral* hota hai — matlab jab bhi app restart/redeploy hoti hai (jaise 15 min inactivity ke baad free tier sleep karke wake hota hai), SQLite database (`instance/sms.db`) **reset ho jaata hai** aur khaali ho jaata hai.

- Demo/project-submission ke liye yeh bilkul thik hai
- Agar **permanent data** chahiye (production use), to Render ka free **PostgreSQL** add-on use karna better hoga, ya MySQL (jaisa form me tha) — us case me `database.py` ko MySQL version pe switch karo aur MySQL hosting (jaise Railway, PlanetScale, ya Render's paid PostgreSQL) use karo.
- Demo ke turant baad data chahiye ho to deploy hote hi ek baar `python seed_data.py` Render Shell se chala sakte ho (Render dashboard → Shell tab).

## Report/Viva ke liye Notes
- **Security:** Passwords hashed hain (Werkzeug), SQL queries parameterized hain (SQL injection se safe)
- **Session-based Auth:** Login zaroori hai har page ke liye (`@login_required` decorator)
- **Live Search:** Students aur Courses dono list pages pe search box hai
- **Pagination:** Real database-driven pagination (10 records per page)
- **Cascading Delete:** Student ya Course delete karne pe uske enrollments bhi automatically delete ho jaate hain
- **Duplicate Protection:** Email (students) aur Course Code (courses) unique hain — duplicate add karne pe error dikhta hai
