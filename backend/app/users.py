from flask import Blueprint, jsonify, request
from app.jwt_auth import jwt_required

from app.sсhemas import user_schema, users_schema

users_bp = Blueprint('users', __name__)

# @users_bp.route('/me', methods = ['GET'])
# @jwt_required
# def get_current_user():
#     user = find_user_by_authID(request.authgear_user_id)
#     if not user:
#         return jsonify({"error": "user not found"}),404
#     return jsonify({"user": {user}})


# @users_bp.route('/set-role', methods = ['POST'])
# @jwt_required
# def set_role():
#     data = request.get_json()
#     role = data.get('role')
#     if role not in ['client', 'specialist']:
#         return jsonify({"error": "invalid role"}), 400
#     if update_user_role(request.authgear_user_id, role):
#         return jsonify({"message": "role set successfully"}), 200
#     else:
#         return jsonify({"error": "user not find"}), 404


# @users_bp.route('/users', methods = ['GET'])
# def get_all_users():
#    result = users_schema.dump(users)
#    return jsonify({
#        "users": result
#    })
    
# @users_bp.route("/users/<user_id>")
# def get_user(user_id):
#     user = find_user_by_authID(user_id)
#     print("DEBUG: user from get_user_by_id =", user)
#     if user is None:
#         return jsonify({"error": "user dont найден"}), 404
#     result = user_schema.dump(user)
#     print("DEBUG: result after dump =", result)
#     return jsonify({"user": result})

    