from app import create_app
from flask import current_app, send_from_directory

app = create_app()


@app.route("/ping")
def ping():
    return "pong"


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
