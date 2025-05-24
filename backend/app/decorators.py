from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            g.user = type('User', (), {
                'id': identity['user_id'],
                'merchant_id': identity['merchant_id'],
                'role': identity['role']
            })
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'code': 1,
                'message': '请先登录'
            }), 401
    return wrapper 