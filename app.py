import os
from flask import Flask, render_template, session, redirect, request, flash

app = Flask(__name__)
app.config["SECRET_KEY"] = "simple-test-key"

# تخزين مؤقت للمستخدمين (للاختبار فقط)
users_db = {}

@app.route("/")
def index():
    return render_template("index.html", db_status="✅ Testing Mode")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Please fill all fields")
            return redirect("/register")
        
        if username in users_db:
            flash("Username already exists")
            return redirect("/register")
        
        users_db[username] = password
        session["username"] = username
        flash("Registration successful! 🎉")
        return redirect("/dashboard")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username in users_db and users_db[username] == password:
            session["username"] = username
            flash("Login successful! 👋")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")
            return redirect("/login")
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    
    return render_template("dashboard.html", username=session["username"])

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)