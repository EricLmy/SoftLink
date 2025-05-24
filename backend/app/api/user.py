from flask import Blueprint, request
from flask_restx import Api, Resource, fields
from app.extensions import db
from app.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

bp = Blueprint('user', __name__)
user_api = Api(bp, prefix='/user', doc='/user/doc', title='子账号管理')

user_model = user_api.model('User', {
    'id': fields.Integer,
    'merchant_id': fields.Integer,
    'username': fields.String,
    'role': fields.String,
    'status': fields.Integer,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
})

user_create_model = user_api.model('UserCreate', {
    'username': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(required=True, description='角色（管理员/员工）'),
    'status': fields.Integer(default=1)
})

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'admin':
            return {'msg': '无权限'}, 403
        return fn(*args, **kwargs)
    return wrapper

@user_api.route('')
@user_api.route('/')
class UserList(Resource):
    @admin_required
    @user_api.marshal_list_with(user_model)
    def get(self):
        identity = get_jwt_identity()
        users = User.query.filter_by(merchant_id=identity['merchant_id']).all()
        return users

    @admin_required
    @user_api.expect(user_create_model)
    def post(self):
        identity = get_jwt_identity()
        data = request.json
        if User.query.filter_by(merchant_id=identity['merchant_id'], username=data['username']).first():
            return {'msg': '用户名已存在'}, 400
        user = User(
            merchant_id=identity['merchant_id'],
            username=data['username'],
            role=data['role'],
            status=data.get('status', 1)
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return {'msg': '创建成功', 'id': user.id}, 201

@user_api.route('/<int:user_id>')
class UserDetail(Resource):
    @admin_required
    @user_api.marshal_with(user_model)
    def get(self, user_id):
        identity = get_jwt_identity()
        user = User.query.filter_by(id=user_id, merchant_id=identity['merchant_id']).first()
        if not user:
            return {'msg': '用户不存在'}, 404
        return user

    @admin_required
    @user_api.expect(user_create_model)
    def put(self, user_id):
        identity = get_jwt_identity()
        user = User.query.filter_by(id=user_id, merchant_id=identity['merchant_id']).first()
        if not user:
            return {'msg': '用户不存在'}, 404
        data = request.json
        user.username = data['username']
        user.role = data['role']
        user.status = data.get('status', user.status)
        if data.get('password'):
            user.set_password(data['password'])
        db.session.commit()
        return {'msg': '更新成功'}

    @admin_required
    def delete(self, user_id):
        identity = get_jwt_identity()
        user = User.query.filter_by(id=user_id, merchant_id=identity['merchant_id']).first()
        if not user:
            return {'msg': '用户不存在'}, 404
        db.session.delete(user)
        db.session.commit()
        return {'msg': '删除成功'}

user_bp = bp
user_api = user_api

__all__ = ['user_bp', 'user_api'] 