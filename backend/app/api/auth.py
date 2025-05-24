from flask import Blueprint, request
from flask_restx import Api, Resource, fields
from app.extensions import db, jwt
from app.models import Merchant, User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_api = Api(auth_bp, title='认证与用户管理')

register_model = auth_api.model('Register', {
    'merchant_name': fields.String(required=True, description='商家名称'),
    'email': fields.String(required=True, description='邮箱'),
    'phone': fields.String(required=True, description='手机号'),
    'username': fields.String(required=True, description='管理员用户名'),
    'password': fields.String(required=True, description='密码')
})

login_model = auth_api.model('Login', {
    'phone': fields.String(required=True, description='手机号'),
    'password': fields.String(required=True, description='密码')
})

user_info_model = auth_api.model('UserInfo', {
    'id': fields.Integer,
    'merchant_id': fields.Integer,
    'username': fields.String,
    'role': fields.String,
    'status': fields.Integer,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
})

@auth_api.route('/register')
class Register(Resource):
    @auth_api.expect(register_model)
    def post(self):
        data = request.json
        # 唯一性校验
        if Merchant.query.filter((Merchant.email == data['email']) | (Merchant.phone == data['phone'])).first():
            return {'msg': '邮箱或手机号已注册'}, 400
        merchant = Merchant(
            name=data['merchant_name'],
            email=data['email'],
            phone=data['phone'],
            password=''  # 先占位
        )
        db.session.add(merchant)
        db.session.flush()  # 获取merchant.id
        user = User(
            merchant_id=merchant.id,
            username=data['username'],
            role='admin',
            status=1
        )
        user.set_password(data['password'])
        merchant.password = user.password  # 商家表也存一份加密密码
        db.session.add(user)
        db.session.commit()
        return {'msg': '注册成功'}, 201

@auth_api.route('/login')
class Login(Resource):
    @auth_api.expect(login_model)
    def post(self):
        data = request.json
        merchant = Merchant.query.filter_by(phone=data['phone']).first()
        if not merchant:
            return {'msg': '用户不存在'}, 404
        # 先查找该商家下的所有用户
        user = User.query.filter_by(merchant_id=merchant.id).first()
        # 如果有传username，优先用username查找
        if data.get('username'):
            user = User.query.filter_by(merchant_id=merchant.id, username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return {'msg': '密码错误'}, 401
        access_token = create_access_token(identity={'user_id': user.id, 'merchant_id': merchant.id, 'role': user.role})
        return {'code': 0, 'message': 'success', 'data': {'token': access_token}}

@auth_api.route('/me')
class Me(Resource):
    @jwt_required()
    @auth_api.marshal_with(user_info_model)
    def get(self):
        identity = get_jwt_identity()
        user = User.query.get(identity['user_id'])
        return user 