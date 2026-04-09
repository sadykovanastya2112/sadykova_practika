
# всё что закоментировано для будующей бд
# from app.extensions import db 
from datetime import datetime

users = [
    {"id": 0, "name": "Damir", "age": 19, "email" : "qwehuy@email.com", "password": "qweqweqweqw1123"},
    {"id": 1, "name": "Tolik", "age": 25, "email" : "goy@email.com", "password": "TRAMDOL12322"},
    {"id": 2, "name": "Ebolik", "age": 44, "email" : "ZVZV@email.com", "password": "EXTAZZZII2135"},
    {"id": 3, "name": "Kachan", "age": 123, "email" : "ldpr@email.com", "password": "LLLLLL55"},
    {"id": 4, "name": "Piska", "age": 6, "email" : "sanyatrava@email.com", "password": "99SHLUXA99"},
    ]

def find_user_by_authID(authgear_id):
    for user in users:
        if user.get('authgear_id') == authgear_id:
            return user
    return None

def create_user_by_authID(authgear_id, email, name):
    new_user = {
        'id': len(users),
        'authgear_id': authgear_id,
        'email': email,
        'name': name,
        'role': None,
        'create_id': datetime.now()
    }
    users.append(new_user)
    return new_user

def update_user_role(authgear_id, role):
    user = find_user_by_authID(authgear_id)
    if user:
        user['role'] = role
        return True
    return False


    

