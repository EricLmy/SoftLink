import pytest
from werkzeug.security import generate_password_hash
from app.models import Merchant, Product, Alert, User
from app.extensions import db
from datetime import datetime

@pytest.fixture
def init_database():
    # 创建商户
    merchant = Merchant(
        name='测试商户',
        phone='13800138000',
        password=generate_password_hash('password')
    )
    db.session.add(merchant)
    db.session.commit()

    # 创建管理员用户
    admin = User(
        username='admin',
        password=generate_password_hash('password'),
        merchant_id=merchant.id,
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()

    # 创建商品
    product = Product(
        merchant_id=merchant.id,
        name='测试商品',
        sku='TEST001',
        price=100,
        stock=10,
        warning_stock=5
    )
    db.session.add(product)
    db.session.commit()

    # 创建告警
    alert = Alert(
        merchant_id=merchant.id,
        product_id=product.id,
        type='stock_warning',
        content='库存不足',
        status='pending'
    )
    db.session.add(alert)
    db.session.commit()

    return {'merchant': merchant, 'admin': admin, 'product': product, 'alert': alert}

def test_get_alert_list_empty(client, init_database):
    """测试获取空告警列表"""
    # 登录
    response = client.post('/api/auth/login', json={
        'phone': '13800138000',
        'password': 'password'
    })
    assert response.status_code == 200
    assert response.json['code'] == 0
    token = response.json['data']['token']

    # 获取告警列表
    response = client.get('/api/alert/', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['code'] == 0
    assert isinstance(response.json['data'], list)

def test_handle_alert(client, init_database):
    """测试处理告警"""
    # 登录
    response = client.post('/api/auth/login', json={
        'phone': '13800138000',
        'password': 'password'
    })
    assert response.status_code == 200
    assert response.json['code'] == 0
    token = response.json['data']['token']

    alert = init_database['alert']
    # 处理告警
    response = client.post(f'/api/alert/{alert.id}/handle', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['code'] == 0
    assert response.json['data']['status'] == 'handled'

def test_handle_nonexistent_alert(client, init_database):
    """测试处理不存在的告警"""
    # 登录
    response = client.post('/api/auth/login', json={
        'phone': '13800138000',
        'password': 'password'
    })
    assert response.status_code == 200
    assert response.json['code'] == 0
    token = response.json['data']['token']

    # 处理不存在的告警
    response = client.post('/api/alert/9999/handle', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    assert response.json['code'] == 1
    assert response.json['message'] == '告警不存在'

def test_create_alert(client, init_database):
    """测试创建告警"""
    # 登录
    response = client.post('/api/auth/login', json={
        'phone': '13800138000',
        'password': 'password'
    })
    assert response.status_code == 200
    assert response.json['code'] == 0
    token = response.json['data']['token']

    product = init_database['product']
    # 创建告警
    response = client.post('/api/alert/', json={
        'product_id': product.id,
        'type': 'stock_warning',
        'content': '库存不足'
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 201
    assert response.json['code'] == 0
    assert response.json['data']['type'] == 'stock_warning' 