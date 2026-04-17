from app import create_app
from app.models import db


app = create_app()

@app.route('/ping')
def ping():
    return "pong"




if __name__ == '__main__':
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        
    