from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
import datetime
import jwt

from ..models import User # 改为相对导入
from ..schemas import UserLoginSchema, UserInfoSchema # 改为相对导入
from .. import db # 改为相对导入
from ..utils import log_activity # 改为相对导入
from ..decorators import token_required # 改为相对导入

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    schema = UserLoginSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as e: # Specific Marshmallow validation error
        return jsonify({"message": "Validation errors", "errors": e.messages}), 400
    except Exception as e:
        return jsonify({"message": "Invalid request format", "errors": str(e)}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        # Log failed login attempt (optional, can generate many logs)
        # log_activity("login_failed", user_id=user.id if user else None, details={"username_attempt": data['username']})
        return jsonify({"message": "Invalid username or password"}), 401

    # Update last login info
    user.last_login_at = datetime.datetime.utcnow()
    user.last_login_ip = request.remote_addr
    # db.session.commit() # Deferred to after log or handled by log_activity

    # Log successful login
    log_activity("user_login_success", user_id=user.id)
    # Note: log_activity does its own commit. If you want a single transaction for user update + log,
    # you might need to pass the db.session to log_activity or handle commit outside.
    # For simplicity here, log_activity commits its own entry.
    # If user.last_login_at commit is separate, ensure it happens:
    db.session.commit() # Ensure user updates and log are committed

    access_token_payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1))
    }
    access_token = jwt.encode(access_token_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    user_info_schema = UserInfoSchema()
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_info": user_info_schema.dump(user)
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    # 记录用户登出活动
    log_activity("user_logout", user_id=current_user.id)
    
    # 在实际应用中，这里可能还需要将token加入黑名单
    # 通常通过Redis或数据库实现token黑名单机制
    # 此处为简化实现，仅记录登出活动
    
    return jsonify({
        "message": "Successfully logged out"
    }), 200

# ... (other auth endpoints) ... 