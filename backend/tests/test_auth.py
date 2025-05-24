import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
from app import create_app, db
from app.models import Merchant, User
from flask_jwt_extended import decode_token
import json

@pytest.fixture(scope='module')
def test_client():
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

# 注册
def test_register(test_client):
    data = {
        'merchant_name': '测试商家',
        'email': 'test@example.com',
        'phone': '13800000000',
        'username': 'admin',
        'password': '12345678'
    }
    resp = test_client.post('/api/auth/register', json=data)
    assert resp.status_code == 201
    assert resp.json['msg'] == '注册成功'

# 注册唯一性校验
def test_register_duplicate(test_client):
    data = {
        'merchant_name': '测试商家2',
        'email': 'test@example.com',
        'phone': '13800000000',
        'username': 'admin2',
        'password': '12345678'
    }
    resp = test_client.post('/api/auth/register', json=data)
    assert resp.status_code == 400
    assert '邮箱或手机号已注册' in resp.json['msg']

# 登录
def test_login(test_client):
    data = {'phone': '13800000000', 'password': '12345678'}
    resp = test_client.post('/api/auth/login', json=data)
    assert resp.status_code == 200
    assert 'data' in resp.json and 'token' in resp.json['data']
    global jwt_token, user_id
    jwt_token = resp.json['data']['token']

# JWT有效性校验
def test_me_auth(test_client):
    headers = {'Authorization': f'Bearer {jwt_token}'}
    resp = test_client.get('/api/auth/me', headers=headers)
    assert resp.status_code == 200

# 未登录访问受保护接口
def test_user_list_unauth(test_client):
    resp = test_client.get('/api/user/')
    assert resp.status_code == 401

# 管理员增删改查子账号
def test_user_crud(test_client):
    headers = {'Authorization': f'Bearer {jwt_token}'}
    # 创建
    data = {'username': 'staff1', 'password': '123456', 'role': '员工', 'status': 1}
    resp = test_client.post('/api/user/', json=data, headers=headers)
    assert resp.status_code == 201
    user_id = resp.json['id']
    # 查询
    resp = test_client.get('/api/user/', headers=headers)
    assert resp.status_code == 200
    # 修改
    data_update = {'username': 'staff1', 'password': '654321', 'role': '员工', 'status': 0}
    resp = test_client.put(f'/api/user/{user_id}', json=data_update, headers=headers)
    assert resp.status_code == 200
    # 删除
    resp = test_client.delete(f'/api/user/{user_id}', headers=headers)
    assert resp.status_code == 200

# 权限校验（员工无权操作）
def test_user_permission(test_client):
    # 创建员工账号
    headers = {'Authorization': f'Bearer {jwt_token}'}
    data = {'username': 'staff2', 'password': '123456', 'role': '员工', 'status': 1}
    resp = test_client.post('/api/user/', json=data, headers=headers)
    assert resp.status_code == 201
    # 员工登录
    login_data = {'phone': '13800000000', 'username': 'staff2', 'password': '123456'}
    resp = test_client.post('/api/auth/login', json=login_data)
    staff_token = resp.json['data']['token']
    staff_headers = {'Authorization': f'Bearer {staff_token}'}
    # 员工尝试增删改查
    resp = test_client.post('/api/user/', json=data, headers=staff_headers)
    assert resp.status_code == 403
    resp = test_client.get('/api/user/', headers=staff_headers)
    assert resp.status_code == 403 