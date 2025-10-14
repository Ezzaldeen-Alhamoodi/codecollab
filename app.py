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

# إعداد قاعدة البيانات بشكل أكثر قوة
def setup_database():
    try:
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://")
            db = SQL(database_url)
            
            # اختبار الاتصال
            db.execute("SELECT 1")
            print("✅ PostgreSQL database connected")
            
            # إنشاء الجداول مع معالجة أفضل للأخطاء
            try:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ Users table created/verified")
            except Exception as e:
                print(f"⚠️ Users table: {e}")

            try:
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
                print("✅ Projects table created/verified")
            except Exception as e:
                print(f"⚠️ Projects table: {e}")

            try:
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
                print("✅ Code files table created/verified")
            except Exception as e:
                print(f"⚠️ Code files table: {e}")
            
            return db, "✅ PostgreSQL - Ready"
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
    
    # استخدام SQLite كبديل
    try:
        db = SQL("sqlite:///codecollab.db")
        print("✅ SQLite database connected")
        
        # إنشاء الجداول في SQLite
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                language TEXT DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS code_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content TEXT,
                language TEXT DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        return db, "✅ SQLite - Fallback Active"
        
    except Exception as e:
        print(f"❌ SQLite also failed: {e}")
        # استخدام قاعدة بيانات في الذاكرة كحل أخير
        db = SQL("sqlite:///:memory:")
        print("✅ Using in-memory SQLite as last resort")
        return db, "⚠️ In-Memory - Limited Functionality"

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
            return apology("يجب إدخال اسم المستخدم", 400)
        if not email:
            return apology("يجب إدخال البريد الإلكتروني", 400)
        if not password:
            return apology("يجب إدخال كلمة المرور", 400)
        if not confirmation:
            return apology("يجب تأكيد كلمة المرور", 400)
        if password != confirmation:
            return apology("كلمات المرور غير متطابقة", 400)
        if len(username) < 3 or len(username) > 20:
            return apology("اسم المستخدم يجب أن يكون بين ٣ و ٢٠ حرف", 400)
        if len(password) < 6:
            return apology("كلمة المرور يجب أن تكون ٦ أحرف على الأقل", 400)

        # التحقق من وجود المستخدم
        try:
            existing_user = db.execute("SELECT id FROM users WHERE username = ?", username)
            if existing_user:
                return apology("اسم المستخدم موجود مسبقاً", 400)

            existing_email = db.execute("SELECT id FROM users WHERE email = ?", email)
            if existing_email:
                return apology("البريد الإلكتروني مسجل مسبقاً", 400)
        except Exception as e:
            print(f"Error checking existing users: {e}")
            return apology("خطأ في التحقق من البيانات", 500)

        # تشفير كلمة المرور وإنشاء المستخدم
        hash_password = generate_password_hash(password)
        
        try:
            # استخدام الطريقة المناسبة لنوع قاعدة البيانات
            if "postgresql" in db_status.lower():
                result = db.execute(
                    "INSERT INTO users (username, email, hash) VALUES (%s, %s, %s) RETURNING id",
                    username, email, hash_password
                )
                user_id = result[0]["id"]
            else:
                # لـ SQLite
                db.execute(
                    "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
                    username, email, hash_password
                )
                # الحصول على آخر معرف تم إدراجه
                result = db.execute("SELECT last_insert_rowid() AS id")
                user_id = result[0]["id"]
            
            session["user_id"] = user_id
            session["username"] = username
            flash("تم التسجيل بنجاح! مرحباً بك في CodeCollab! 🎉")
            return redirect("/dashboard")
            
        except Exception as e:
            print(f"Registration error: {e}")
            return apology("فشل في التسجيل - حاول مرة أخرى", 500)

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("يجب إدخال اسم المستخدم", 403)
        if not password:
            return apology("يجب إدخال كلمة المرور", 403)

        try:
            users = db.execute("SELECT * FROM users WHERE username = ?", username)

            if len(users) != 1:
                return apology("اسم المستخدم أو كلمة المرور غير صحيحة", 403)
                
            if not check_password_hash(users[0]["hash"], password):
                return apology("اسم المستخدم أو كلمة المرور غير صحيحة", 403)

            session["user_id"] = users[0]["id"]
            session["username"] = users[0]["username"]
            flash(f"مرحباً بعودتك، {username}! 👋")
            return redirect("/dashboard")

        except Exception as e:
            print(f"Login error: {e}")
            return apology("خطأ في تسجيل الدخول - حاول مرة أخرى", 500)

    return render_template("login.html")

# باقي الكود يبقى كما هو...
@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج بنجاح")
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    
    try:
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
    except Exception as e:
        print(f"Dashboard error: {e}")
        return apology("خطأ في تحميل لوحة التحكم", 500)

# باقي routes تبقى كما هي...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)