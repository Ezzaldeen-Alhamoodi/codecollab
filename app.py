import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from cs50 import SQL

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "codecollab-secret-2025")

# إعداد قاعدة البيانات بشكل آمن
try:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://")
        db = SQL(database_url)
        # اختبار الاتصال وإنشاء الجداول
        db.execute("SELECT 1")
        print("✅ PostgreSQL database connected")
        
        # إنشاء الجداول إذا لم تكن موجودة
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                owner_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                language VARCHAR(50) DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS code_files (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL,
                filename VARCHAR(200) NOT NULL,
                content TEXT,
                language VARCHAR(50) DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db_status = "✅ PostgreSQL - Tables Ready"
        
except Exception as e:
    print(f"Database error: {e}")
    # استخدام SQLite كبديل
    db = SQL("sqlite:///codecollab.db")
    db_status = "✅ SQLite - Fallback Active"

@app.route("/")
def index():
    return render_template("index.html", db_status=db_status)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Please fill all fields")
            return redirect("/register")
        
        try:
            # في الإصدار الحقيقي، يجب تشفير كلمة المرور
            user_id = db.execute(
                "INSERT INTO users (username, email, hash) VALUES (?, ?, ?) RETURNING id",
                username, f"{username}@example.com", password
            )
            
            session["user_id"] = user_id
            session["username"] = username
            flash("Registration successful! 🎉")
            return redirect("/dashboard")
            
        except Exception as e:
            flash("Username already exists")
            return redirect("/register")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        
        if user and user[0]["hash"] == password:  # في الإصدار الحقيقي، استخدام تشفير
            session["user_id"] = user[0]["id"]
            session["username"] = user[0]["username"]
            flash("Login successful! 👋")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")
            return redirect("/login")
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    # جلب مشاريع المستخدم
    projects = db.execute(
        "SELECT * FROM projects WHERE owner_id = ? ORDER BY created_at DESC", 
        session["user_id"]
    )
    
    return render_template("dashboard.html", 
                         username=session["username"], 
                         projects=projects)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)