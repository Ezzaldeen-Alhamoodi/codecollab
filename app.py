import os
from flask import Flask, render_template

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test-secret-key")

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CodeCollab - Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="#">CodeCollab</a>
            </div>
        </nav>
        <div class="container mt-5">
            <h1>🚀 CodeCollab - Test Deployment</h1>
            <div class="alert alert-success">
                <strong>Status:</strong> Basic app is working! 
                Database connection will be added next.
            </div>
            <p>Developed by <strong>Ezzaldeen Nashwan Ali Alhamoodi</strong></p>
            <p>CS50x 2025 Final Project</p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)