from app import create_app
from app.models import db
from flask import current_app, send_from_directory
import sys


app = create_app()

sys.path.insert(0, '/workspaces/safe-contact-1/backend')

@app.route("/ping")
def ping():
    return "pong"


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
    
