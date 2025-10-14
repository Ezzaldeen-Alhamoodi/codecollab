import os
from flask import Flask, render_template, session, redirect, request, flash, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "simple-test-key-12345")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# تخزين مؤقت للمستخدمين (في الذاكرة)
users_db = {
    "testuser": "testpass123",
    "admin": "admin123"
}

@app.route("/")
def index():
    return render_template("index.html", db_status="✅ Simple Test Mode")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            
            print(f"Registration attempt: {username}")
            
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
            
            # حفظ المستخدم الجديد
            users_db[username] = password
            session["username"] = username
            session["user_id"] = len(users_db)  # ID بسيط
            
            flash("🎉 Registration successful! Welcome to CodeCollab!")
            return redirect("/dashboard")
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash("❌ Registration failed. Please try again.")
            return redirect("/register")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            
            print(f"Login attempt: {username}")
            
            if not username or not password:
                flash("⚠️ Please fill in all fields")
                return redirect("/login")
            
            if username in users_db and users_db[username] == password:
                session["username"] = username
                session["user_id"] = list(users_db.keys()).index(username) + 1
                flash(f"👋 Welcome back, {username}!")
                return redirect("/dashboard")
            else:
                flash("❌ Invalid username or password")
                return redirect("/login")
                
        except Exception as e:
            print(f"Login error: {e}")
            flash("❌ Login failed. Please try again.")
            return redirect("/login")
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("🔒 Please log in first")
        return redirect("/login")
    
    user_projects = [
        {"id": 1, "title": "My First Project", "language": "python", "description": "Getting started with CodeCollab"},
        {"id": 2, "title": "Web App", "language": "javascript", "description": "Building a web application"}
    ]
    
    stats = {
        "projects_count": len(user_projects),
        "total_files": 5
    }
    
    return render_template("dashboard.html", 
                         username=session["username"],
                         projects=user_projects,
                         stats=stats)

@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Logged out successfully")
    return redirect("/")

# صفحة بسيطة للتعريف بالمطور
@app.route("/about")
def about():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - CodeCollab</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">CodeCollab</a>
            </div>
        </nav>
        <div class="container mt-5">
            <h1>About CodeCollab</h1>
            <div class="card">
                <div class="card-body">
                    <h5>Developer Information</h5>
                    <p><strong>Name:</strong> Ezzaldeen Nashwan Ali Alhamoodi</p>
                    <p><strong>Project:</strong> CS50x 2025 Final Project</p>
                    <p><strong>Description:</strong> A collaborative coding platform for developers.</p>
                    <a href="/" class="btn btn-primary">Back to Home</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# معالج للأخطاء
@app.errorhandler(500)
def internal_error(error):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error - CodeCollab</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="alert alert-danger">
                <h4>Internal Server Error</h4>
                <p>Something went wrong. Please try again later.</p>
                <a href="/" class="btn btn-primary">Go Home</a>
            </div>
        </div>
    </body>
    </html>
    """, 500

@app.errorhandler(404)
def not_found(error):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Not Found - CodeCollab</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="alert alert-warning">
                <h4>Page Not Found</h4>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/" class="btn btn-primary">Go Home</a>
            </div>
        </div>
    </body>
    </html>
    """, 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting CodeCollab on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)