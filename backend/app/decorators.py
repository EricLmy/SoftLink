from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                 return jsonify({'message': 'Token is invalid or user not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            current_app.logger.error(f"Token validation error: {e}")
            return jsonify({'message': 'Token validation failed!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# Decorator for optional token (e.g., for anonymous feedback)
def optional_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
                if token:
                    try:
                        data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
                        current_user = User.query.get(data['user_id'])
                    except Exception:
                        # If token is present but invalid, it's an error for optional auth?
                        # Or just proceed as anonymous? For feedback, maybe proceed as anonymous.
                        # Let's treat invalid optional token as anonymous for now.
                        current_user = None 
        return f(current_user, *args, **kwargs)
    return decorated

# Decorator to check user role/permissions
def permission_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = ['super_admin'] # Default to super_admin if no roles specified

    def decorator(f):
        @wraps(f)
        @token_required # Ensures user is authenticated
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({'message': 'Permission denied. Required roles: {}'.format(", ".join(allowed_roles))}), 403
            # More granular permission check can be added here later by checking current_user against Permission and RolePermission tables
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator 