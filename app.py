import os
from flask import Flask, render_template, session, redirect, request, flash, url_for, jsonify
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "codecollab-secret-2025")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# تخزين البيانات في الذاكرة (للنسخة المبسطة)
users_db = {
    "testuser": "testpass123",
    "admin": "admin123"
}

projects_db = {}
files_db = {}
project_counter = 1
file_counter = 1

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("🔒 Please log in first")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    if "username" in session:
        return redirect("/dashboard")
    return render_template("index.html", db_status="✅ Simple Mode - Working")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            
            if not username or not password:
                flash("⚠️ Please fill in all fields")
                return redirect("/register")
            
            if len(username) < 3:
                flash("⚠️ Username must be at least 3 characters")
                return redirect("/register")
            
            if len(password) < 3:
                flash("⚠️ Password must be at least 3 characters")
                return redirect("/register")
            
            if username in users_db:
                flash("⚠️ Username already exists")
                return redirect("/register")
            
            users_db[username] = password
            session["username"] = username
            session["user_id"] = len(users_db)
            
            flash("🎉 Registration successful! Welcome to CodeCollab!")
            return redirect("/dashboard")
            
        except Exception as e:
            flash("❌ Registration failed. Please try again.")
            return redirect("/register")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            
            if username in users_db and users_db[username] == password:
                session["username"] = username
                session["user_id"] = list(users_db.keys()).index(username) + 1
                flash(f"👋 Welcome back, {username}!")
                return redirect("/dashboard")
            else:
                flash("❌ Invalid username or password")
                return redirect("/login")
                
        except Exception as e:
            flash("❌ Login failed. Please try again.")
            return redirect("/login")
    
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    username = session["username"]
    user_projects = []
    
    # جلب مشاريع المستخدم
    for project_id, project in projects_db.items():
        if project["owner"] == username:
            user_projects.append(project)
    
    stats = {
        "projects_count": len(user_projects),
        "total_files": sum(len(project.get("files", [])) for project in user_projects)
    }
    
    return render_template("dashboard.html", 
                         username=username,
                         projects=user_projects,
                         stats=stats)

@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            language = request.form.get("language", "python")
            
            if not title:
                flash("⚠️ Project title is required")
                return redirect("/projects/new")
            
            global project_counter
            project_id = project_counter
            project_counter += 1
            
            # إنشاء المشروع
            projects_db[project_id] = {
                "id": project_id,
                "title": title,
                "description": description,
                "language": language,
                "owner": session["username"],
                "files": []
            }
            
            # إنشاء ملف افتراضي
            global file_counter
            file_id = file_counter
            file_counter += 1
            
            default_content = {
                "python": "# Welcome to your Python project!\n\nprint('Hello, CodeCollab!')\n",
                "javascript": "// Welcome to your JavaScript project!\n\nconsole.log('Hello, CodeCollab!');\n",
                "html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>My Project</title>\n</head>\n<body>\n    <h1>Hello, CodeCollab!</h1>\n</body>\n</html>\n",
                "java": "// Welcome to your Java project!\n\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, CodeCollab!\");\n    }\n}\n"
            }
            
            filename = {
                "python": "main.py",
                "javascript": "app.js", 
                "html": "index.html",
                "java": "Main.java"
            }.get(language, "main.txt")
            
            files_db[file_id] = {
                "id": file_id,
                "project_id": project_id,
                "filename": filename,
                "content": default_content.get(language, "# Start coding here...\n"),
                "language": language
            }
            
            projects_db[project_id]["files"].append(file_id)
            
            flash(f"🎉 Project '{title}' created successfully!")
            return redirect(f"/project/{project_id}")
            
        except Exception as e:
            flash("❌ Failed to create project")
            return redirect("/projects/new")
    
    return render_template("new_project.html")

@app.route("/project/<int:project_id>")
@login_required
def view_project(project_id):
    username = session["username"]
    
    if project_id not in projects_db:
        flash("❌ Project not found")
        return redirect("/dashboard")
    
    project = projects_db[project_id]
    
    # التحقق من ملكية المشروع
    if project["owner"] != username:
        flash("❌ Access denied")
        return redirect("/dashboard")
    
    # جلب ملفات المشروع
    project_files = []
    for file_id in project["files"]:
        if file_id in files_db:
            project_files.append(files_db[file_id])
    
    return render_template("project.html", 
                         project=project, 
                         files=project_files)

@app.route("/editor/<int:project_id>/<int:file_id>")
@login_required
def code_editor(project_id, file_id):
    username = session["username"]
    
    # التحقق من وجود المشروع والملف
    if project_id not in projects_db or file_id not in files_db:
        flash("❌ File not found")
        return redirect("/dashboard")
    
    project = projects_db[project_id]
    file_data = files_db[file_id]
    
    # التحقق من الملكية
    if project["owner"] != username or file_data["project_id"] != project_id:
        flash("❌ Access denied")
        return redirect("/dashboard")
    
    # جلب جميع ملفات المشروع للشريط الجانبي
    project_files = []
    for fid in project["files"]:
        if fid in files_db:
            project_files.append(files_db[fid])
    
    return render_template("editor.html",
                         project=project,
                         file=file_data,
                         project_files=project_files)

@app.route("/api/save_code", methods=["POST"])
@login_required
def save_code():
    try:
        file_id = request.json.get("file_id")
        content = request.json.get("content")
        
        if not file_id or file_id not in files_db:
            return jsonify({"success": False, "error": "File not found"})
        
        # تحديث محتوى الملف
        files_db[file_id]["content"] = content
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"success": False, "error": "Save failed"})

@app.route("/api/create_file", methods=["POST"])
@login_required
def create_file():
    try:
        project_id = request.json.get("project_id")
        filename = request.json.get("filename")
        
        if not project_id or not filename:
            return jsonify({"success": False, "error": "Missing data"})
        
        if project_id not in projects_db:
            return jsonify({"success": False, "error": "Project not found"})
        
        # إنشاء ملف جديد
        global file_counter
        file_id = file_counter
        file_counter += 1
        
        files_db[file_id] = {
            "id": file_id,
            "project_id": project_id,
            "filename": filename,
            "content": f"# {filename}\n\n# Start coding here...\n",
            "language": "text"
        }
        
        projects_db[project_id]["files"].append(file_id)
        
        return jsonify({"success": True, "file_id": file_id})
        
    except Exception as e:
        return jsonify({"success": False, "error": "File creation failed"})

@app.route("/profile")
@login_required
def profile():
    username = session["username"]
    
    # حساب الإحصائيات
    user_projects = [p for p in projects_db.values() if p["owner"] == username]
    total_files = sum(len(p.get("files", [])) for p in user_projects)
    
    stats = {
        "project_count": len(user_projects),
        "file_count": total_files
    }
    
    return render_template("profile.html", 
                         username=username, 
                         stats=stats)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Logged out successfully")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting CodeCollab on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)