from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="#">Test App</a>
            </div>
        </nav>
        <div class="container mt-5">
            <h1>Hello World! 🎉</h1>
            <p>If you can see this, Flask is working perfectly!</p>
            <a href="/register" class="btn btn-primary">Test Register</a>
        </div>
    </body>
    </html>
    ''')

@app.route("/register")
def register():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2>Register Test</h2>
            <p>This is a test registration page.</p>
            <form>
                <input type="text" class="form-control mb-2" placeholder="Username">
                <input type="password" class="form-control mb-2" placeholder="Password">
                <button class="btn btn-success">Register</button>
            </form>
        </div>
    </body>
    </html>
    ''')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
