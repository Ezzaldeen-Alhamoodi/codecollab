import os
import re
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, apology

app = Flask(__name__)

# استخدام متغير بيئي للسرية (مهم للأمان)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "codecollab_secret_key_2025")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# استخدام قاعدة بيانات من البيئة أو المحلية
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # إذا كان هناك DATABASE_URL (في الخوادم) استخدمه
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://")
    db = SQL(database_url)
    # إنشاء الجداول إذا لم تكن موجودة في PostgreSQL
    try:
        db.execute("SELECT 1 FROM users LIMIT 1")
    except:
        # الجداول غير موجودة، فلننشئها
        db.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE projects (
                id SERIAL PRIMARY KEY,
                owner_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                language VARCHAR(50) DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_public BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        db.execute("""
            CREATE TABLE code_files (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL,
                filename VARCHAR(200) NOT NULL,
                content TEXT,
                language VARCHAR(50) DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        db.execute("""
            CREATE TABLE project_members (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(20) DEFAULT 'collaborator',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(project_id, user_id)
            )
        """)
else:
    # وإلا استخدم SQLite محلي
    db = SQL("sqlite:///codecollab.db")

app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    # إذا كان المستخدم مسجل الدخول، أظهر لوحة التحكم
    if session.get("user_id"):
        return redirect("/dashboard")

    # إذا لم يكن مسجل الدخول، أظهر الصفحة الرئيسية
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard for logged-in users"""
    user_id = session["user_id"]

    # Get user info
    user = db.execute("SELECT username FROM users WHERE id = ?", user_id)[0]

    # Get user's projects
    projects = db.execute("""
        SELECT * FROM projects
        WHERE owner_id = ?
        ORDER BY created_at DESC
    """, user_id)

    return render_template("dashboard.html", user=user, projects=projects)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate inputs
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

        # Check username length
        if len(username) < 3 or len(username) > 20:
            return apology("username must be between 3 and 20 characters", 400)

        # Check password length
        if len(password) < 6:
            return apology("password must be at least 6 characters", 400)

        # Check if username already exists
        existing_user = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing_user:
            return apology("username already exists", 400)

        # Check if email already exists
        existing_email = db.execute("SELECT id FROM users WHERE email = ?", email)
        if existing_email:
            return apology("email already registered", 400)

        # Hash password
        hash_password = generate_password_hash(password)

        # Insert new user
        try:
            # لـ PostgreSQL نستخدم RETURNING id للحصول على الـ ID
            if database_url and "postgresql" in database_url:
                result = db.execute(
                    "INSERT INTO users (username, email, hash) VALUES (%s, %s, %s) RETURNING id",
                    username, email, hash_password
                )
                user_id = result[0]["id"]
            else:
                # لـ SQLite
                user_id = db.execute(
                    "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
                    username, email, hash_password
                )

            # Log user in
            session["user_id"] = user_id

            flash("Registration successful! Welcome to CodeCollab! 🎉")
            return redirect("/dashboard")

        except Exception as e:
            print(f"Registration error: {e}")
            return apology("registration failed", 500)

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash(f"Welcome back, {username}! 👋")
        return redirect("/dashboard")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    flash("You have been logged out successfully.")
    return redirect("/")

@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():
    """Create new project with default file"""

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        language = request.form.get("language", "python")

        if not title:
            return apology("must provide project title", 400)

        user_id = session["user_id"]

        try:
            # Create project
            if database_url and "postgresql" in database_url:
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

            # Create default main file based on language
            default_files = {
                "python": ("main.py", "# Welcome to your Python project!\n\nprint('Hello, CodeCollab!')"),
                "javascript": ("app.js", "// Welcome to your JavaScript project!\n\nconsole.log('Hello, CodeCollab!');"),
                "html": ("index.html", "<!DOCTYPE html>\n<html>\n<head>\n    <title>My Project</title>\n</head>\n<body>\n    <h1>Hello, CodeCollab!</h1>\n</body>\n</html>"),
                "java": ("Main.java", "// Welcome to your Java project!\n\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, CodeCollab!\");\n    }\n}")
            }

            filename, content = default_files.get(language, ("main.txt", "# Start coding here..."))

            # Create the default file
            db.execute(
                "INSERT INTO code_files (project_id, filename, content, language) VALUES (?, ?, ?, ?)",
                project_id, filename, content, language
            )

            flash(f"Project '{title}' created successfully! 🎉")
            return redirect(f"/project/{project_id}")

        except Exception as e:
            print(f"Project creation error: {e}")
            return apology("failed to create project", 500)

    else:
        return render_template("new_project.html")

@app.route("/project/<int:project_id>")
@login_required
def view_project(project_id):
    """View project details and files"""
    user_id = session["user_id"]

    # Check if user has access to project
    project = db.execute("""
        SELECT * FROM projects
        WHERE id = ? AND owner_id = ?
    """, project_id, user_id)

    if not project:
        return apology("Project not found or access denied", 403)

    project = project[0]

    # Get project files
    files = db.execute("""
        SELECT * FROM code_files
        WHERE project_id = ?
        ORDER BY filename
    """, project_id)

    return render_template("project.html", project=project, files=files)

@app.route("/editor/<int:project_id>/<int:file_id>")
@login_required
def code_editor(project_id, file_id):
    """Code editor page"""
    user_id = session["user_id"]

    # Verify access
    file_data = db.execute("""
        SELECT cf.*, p.title as project_title
        FROM code_files cf
        JOIN projects p ON cf.project_id = p.id
        WHERE cf.id = ? AND p.owner_id = ?
    """, file_id, user_id)

    if not file_data:
        return apology("File not found or access denied", 403)

    file_data = file_data[0]

    # Get all files in project for sidebar
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
    """Save code content via AJAX"""
    file_id = request.json.get("file_id")
    content = request.json.get("content")

    if not file_id or content is None:
        return jsonify({"success": False, "error": "Missing data"})

    user_id = session["user_id"]

    # Verify ownership
    file_check = db.execute("""
        SELECT cf.id FROM code_files cf
        JOIN projects p ON cf.project_id = p.id
        WHERE cf.id = ? AND p.owner_id = ?
    """, file_id, user_id)

    if not file_check:
        return jsonify({"success": False, "error": "Access denied"})

    # Update file content
    db.execute("""
        UPDATE code_files
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, content, file_id)

    return jsonify({"success": True})

@app.route("/api/create_file", methods=["POST"])
@login_required
def create_file():
    """Create new file in project"""
    project_id = request.json.get("project_id")
    filename = request.json.get("filename")

    if not project_id or not filename:
        return jsonify({"success": False, "error": "Missing data"})

    user_id = session["user_id"]

    # Verify ownership
    project_check = db.execute("""
        SELECT id FROM projects WHERE id = ? AND owner_id = ?
    """, project_id, user_id)

    if not project_check:
        return jsonify({"success": False, "error": "Access denied"})

    # Create file
    try:
        if database_url and "postgresql" in database_url:
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
        print(f"File creation error: {e}")
        return jsonify({"success": False, "error": "File creation failed"})

@app.route("/about")
def about():
    """About page with developer information"""
    return render_template("about.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    