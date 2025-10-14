import os
import re
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

# استخدام متغير بيئي للسرية
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "codecollab-secret-2025")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# إعداد قاعدة البيانات
def setup_database():
    try:
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://")
            db = SQL(database_url)
            print("✅ PostgreSQL database connected")
            
            # إنشاء الجداول
            tables_sql = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    language VARCHAR(50) DEFAULT 'python',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS code_files (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    filename VARCHAR(200) NOT NULL,
                    content TEXT,
                    language VARCHAR(50) DEFAULT 'python',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]
            
            for sql in tables_sql:
                try:
                    db.execute(sql)
                except:
                    pass
            
            return db, "✅ PostgreSQL - Ready"
            
    except Exception as e:
        print(f"Database error: {e}")
    
    # استخدام SQLite كبديل
    db = SQL("sqlite:///codecollab.db")
    return db, "✅ SQLite - Fallback Active"

db, db_status = setup_database()

# دالة للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# دالة للاعتذار
def apology(message, code=400):
    return render_template("apology.html", message=message, code=code), code

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("index.html", db_status=db_status)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)
        if not email:
            return apology("must provide email", 400)
        if not password:
            return apology("must provide password", 400)
        if not confirmation:
            return apology("must confirm password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)
        if len(username) < 3 or len(username) > 20:
            return apology("username must be between 3 and 20 characters", 400)
        if len(password) < 6:
            return apology("password must be at least 6 characters", 400)

        # التحقق من وجود المستخدم
        existing_user = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing_user:
            return apology("username already exists", 400)

        existing_email = db.execute("SELECT id FROM users WHERE email = ?", email)
        if existing_email:
            return apology("email already registered", 400)

        # تشفير كلمة المرور وإنشاء المستخدم
        hash_password = generate_password_hash(password)
        
        try:
            if "postgresql" in db_status.lower():
                result = db.execute(
                    "INSERT INTO users (username, email, hash) VALUES (%s, %s, %s) RETURNING id",
                    username, email, hash_password
                )
                user_id = result[0]["id"]
            else:
                user_id = db.execute(
                    "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
                    username, email, hash_password
                )
            
            session["user_id"] = user_id
            session["username"] = username
            flash("Registration successful! Welcome to CodeCollab! 🎉")
            return redirect("/dashboard")
            
        except Exception as e:
            return apology("registration failed", 500)

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)

        users = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(users) != 1 or not check_password_hash(users[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        session["user_id"] = users[0]["id"]
        session["username"] = users[0]["username"]
        flash(f"Welcome back, {username}! 👋")
        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    
    # جلب مشاريع المستخدم
    projects = db.execute(
        "SELECT * FROM projects WHERE owner_id = ? ORDER BY created_at DESC", 
        user_id
    )
    
    # إحصائيات المستخدم
    stats = {
        "projects_count": len(projects),
        "total_files": 0
    }
    
    for project in projects:
        files = db.execute("SELECT COUNT(*) as count FROM code_files WHERE project_id = ?", project["id"])
        stats["total_files"] += files[0]["count"] if files else 0
    
    return render_template("dashboard.html", 
                         username=session["username"], 
                         projects=projects,
                         stats=stats)

@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        language = request.form.get("language", "python")

        if not title:
            return apology("must provide project title", 400)

        user_id = session["user_id"]

        try:
            # إنشاء المشروع
            if "postgresql" in db_status.lower():
                result = db.execute(
                    "INSERT INTO projects (owner_id, title, description, language) VALUES (%s, %s, %s, %s) RETURNING id",
                    user_id, title, description, language
                )
                project_id = result[0]["id"]
            else:
                project_id = db.execute(
                    "INSERT INTO projects (owner_id, title, description, language) VALUES (?, ?, ?, ?)",
                    user_id, title, description, language
                )

            # إنشاء ملف افتراضي بناءً على اللغة
            default_files = {
                "python": ("main.py", "# Welcome to your Python project!\n\nprint('Hello, CodeCollab!')"),
                "javascript": ("app.js", "// Welcome to your JavaScript project!\n\nconsole.log('Hello, CodeCollab!');"),
                "html": ("index.html", "<!DOCTYPE html>\n<html>\n<head>\n    <title>My Project</title>\n</head>\n<body>\n    <h1>Hello, CodeCollab!</h1>\n</body>\n</html>"),
                "java": ("Main.java", "// Welcome to your Java project!\n\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, CodeCollab!\");\n    }\n}")
            }

            filename, content = default_files.get(language, ("main.txt", "# Start coding here..."))

            # إنشاء الملف الافتراضي
            db.execute(
                "INSERT INTO code_files (project_id, filename, content, language) VALUES (?, ?, ?, ?)",
                project_id, filename, content, language
            )

            flash(f"Project '{title}' created successfully! 🎉")
            return redirect(f"/project/{project_id}")

        except Exception as e:
            return apology("failed to create project", 500)

    return render_template("new_project.html")

@app.route("/project/<int:project_id>")
@login_required
def view_project(project_id):
    user_id = session["user_id"]
    
    # التحقق من صلاحية الوصول
    project = db.execute("SELECT * FROM projects WHERE id = ? AND owner_id = ?", project_id, user_id)
    if not project:
        return apology("Project not found or access denied", 403)

    project = project[0]
    
    # جلب ملفات المشروع
    files = db.execute("SELECT * FROM code_files WHERE project_id = ? ORDER BY filename", project_id)

    return render_template("project.html", project=project, files=files)

@app.route("/editor/<int:project_id>/<int:file_id>")
@login_required
def code_editor(project_id, file_id):
    user_id = session["user_id"]

    # التحقق من صلاحية الوصول
    file_data = db.execute("""
        SELECT cf.*, p.title as project_title
        FROM code_files cf
        JOIN projects p ON cf.project_id = p.id
        WHERE cf.id = ? AND p.owner_id = ?
    """, file_id, user_id)

    if not file_data:
        return apology("File not found or access denied", 403)

    file_data = file_data[0]

    # جلب جميع ملفات المشروع للشريط الجانبي
    project_files = db.execute("""
        SELECT id, filename FROM code_files
        WHERE project_id = ?
        ORDER BY filename
    """, project_id)

    return render_template("editor.html",
                         file=file_data,
                         project_files=project_files,
                         project_id=project_id)

@app.route("/api/save_code", methods=["POST"])
@login_required
def save_code():
    """حفظ المحتوى عبر AJAX"""
    file_id = request.json.get("file_id")
    content = request.json.get("content")

    if not file_id or content is None:
        return jsonify({"success": False, "error": "Missing data"})

    user_id = session["user_id"]

    # التحقق من الملكية
    file_check = db.execute("""
        SELECT cf.id FROM code_files cf
        JOIN projects p ON cf.project_id = p.id
        WHERE cf.id = ? AND p.owner_id = ?
    """, file_id, user_id)

    if not file_check:
        return jsonify({"success": False, "error": "Access denied"})

    # تحديث محتوى الملف
    db.execute("""
        UPDATE code_files
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, content, file_id)

    return jsonify({"success": True})

@app.route("/api/create_file", methods=["POST"])
@login_required
def create_file():
    """إنشاء ملف جديد في المشروع"""
    project_id = request.json.get("project_id")
    filename = request.json.get("filename")

    if not project_id or not filename:
        return jsonify({"success": False, "error": "Missing data"})

    user_id = session["user_id"]

    # التحقق من الملكية
    project_check = db.execute("""
        SELECT id FROM projects WHERE id = ? AND owner_id = ?
    """, project_id, user_id)

    if not project_check:
        return jsonify({"success": False, "error": "Access denied"})

    # إنشاء الملف
    try:
        if "postgresql" in db_status.lower():
            result = db.execute("""
                INSERT INTO code_files (project_id, filename, content)
                VALUES (%s, %s, %s) RETURNING id
            """, project_id, filename, f"# {filename}\n\n# Start coding here...")
            file_id = result[0]["id"]
        else:
            file_id = db.execute("""
                INSERT INTO code_files (project_id, filename, content)
                VALUES (?, ?, ?)
            """, project_id, filename, f"# {filename}\n\n# Start coding here...")

        return jsonify({"success": True, "file_id": file_id})

    except Exception as e:
        return jsonify({"success": False, "error": "File creation failed"})

@app.route("/profile")
@login_required
def profile():
    """صفحة الملف الشخصي"""
    user_id = session["user_id"]
    user = db.execute("SELECT username, email, created_at FROM users WHERE id = ?", user_id)[0]
    
    # إحصائيات المستخدم
    stats = db.execute("""
        SELECT 
            COUNT(DISTINCT p.id) as project_count,
            COUNT(DISTINCT cf.id) as file_count
        FROM users u
        LEFT JOIN projects p ON u.id = p.owner_id
        LEFT JOIN code_files cf ON p.id = cf.project_id
        WHERE u.id = ?
    """, user_id)[0]
    
    return render_template("profile.html", user=user, stats=stats)

@app.route("/about")
def about():
    """صفحة حول التطبيق"""
    return render_template("about.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)