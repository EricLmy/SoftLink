import pytest
from app import create_app, db
from app.models import Order, OrderItem, Product, Inventory, Merchant
from datetime import datetime
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()
        
        # 创建测试商户
        merchant = Merchant(
            name='测试商户',
            email='test@example.com',
            phone='13800138002',
            password=generate_password_hash('123456')
        )
        db.session.add(merchant)
        db.session.flush()
        
        # 创建测试商品
        product = Product(
            merchant_id=merchant.id,
            name='测试商品',
            sku='TEST001',
            unit='个',
            price=100
        )
        db.session.add(product)
        db.session.flush()
        
        # 创建测试库存
        inventory = Inventory(
            merchant_id=merchant.id,
            product_id=product.id,
            quantity=100,
            warning_line=10
        )
        db.session.add(inventory)
        db.session.commit()
        
        yield
        
        db.session.remove()
        db.drop_all()

def test_get_order_list_empty(client, init_database):
    """测试获取空订单列表"""
    response = client.get('/api/order')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    assert len(json_data['data']) == 0

def test_create_order(client, init_database):
    """测试创建订单"""
    # 获取测试商品
    with client.application.app_context():
        product = Product.query.first()
        
    # 创建订单数据
    data = {
        'customer_name': '测试客户',
        'customer_phone': '13900139000',
        'items': [
            {
                'product_id': product.id,
                'quantity': 2,
                'price': 99.99
            }
        ],
        'remark': '测试订单'
    }
    
    response = client.post('/api/order', json=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    assert 'order_id' in json_data['data']
    assert 'order_no' in json_data['data']
    
    # 验证订单是否创建成功
    with client.application.app_context():
        order = Order.query.get(json_data['data']['order_id'])
        assert order is not None
        assert order.customer_name == '测试客户'
        assert order.customer_phone == '13900139000'
        assert order.status == 'pending'
        assert float(order.total_amount) == 199.98  # 2 * 99.99
        
        # 验证订单明细
        order_item = OrderItem.query.filter_by(order_id=order.id).first()
        assert order_item is not None
        assert order_item.product_id == product.id
        assert order_item.quantity == 2
        assert float(order_item.price) == 99.99
        assert float(order_item.amount) == 199.98
        
        # 验证库存是否扣减
        inventory = Inventory.query.filter_by(product_id=product.id).first()
        assert inventory.quantity == 98  # 100 - 2

def test_create_order_with_invalid_product(client, init_database):
    """测试创建订单时使用不存在的商品"""
    data = {
        'customer_name': '测试客户',
        'customer_phone': '13900139000',
        'items': [
            {
                'product_id': 9999,  # 不存在的商品ID
                'quantity': 2,
                'price': 99.99
            }
        ],
        'remark': '测试订单'
    }
    
    response = client.post('/api/order', json=data)
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['code'] == 404
    assert '不存在' in json_data['message']

def test_create_order_with_insufficient_inventory(client, init_database):
    """测试创建订单时库存不足"""
    with client.application.app_context():
        product = Product.query.first()
        
    data = {
        'customer_name': '测试客户',
        'customer_phone': '13900139000',
        'items': [
            {
                'product_id': product.id,
                'quantity': 999,  # 大于库存数量
                'price': 99.99
            }
        ],
        'remark': '测试订单'
    }
    
    response = client.post('/api/order', json=data)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['code'] == 400
    assert '库存不足' in json_data['message']

def test_get_order_detail(client, init_database):
    """测试获取订单详情"""
    # 先创建一个订单
    with client.application.app_context():
        product = Product.query.first()
        
    data = {
        'customer_name': '测试客户',
        'customer_phone': '13900139000',
        'items': [
            {
                'product_id': product.id,
                'quantity': 2,
                'price': 99.99
            }
        ],
        'remark': '测试订单'
    }
    
    response = client.post('/api/order', json=data)
    order_id = response.get_json()['data']['order_id']
    
    # 获取订单详情
    response = client.get(f'/api/order/{order_id}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    assert json_data['data']['id'] == order_id
    assert json_data['data']['customer_name'] == '测试客户'
    assert len(json_data['data']['items']) == 1
    assert json_data['data']['items'][0]['quantity'] == 2

def test_update_order_status(client, init_database):
    """测试更新订单状态"""
    # 先创建一个订单
    with client.application.app_context():
        product = Product.query.first()
        
    data = {
        'customer_name': '测试客户',
        'customer_phone': '13900139000',
        'items': [
            {
                'product_id': product.id,
                'quantity': 2,
                'price': 99.99
            }
        ],
        'remark': '测试订单'
    }
    
    response = client.post('/api/order', json=data)
    order_id = response.get_json()['data']['order_id']
    
    # 更新订单状态
    response = client.post(f'/api/order/{order_id}/status', json={'status': 'processing'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    
    # 验证订单状态是否更新
    with client.application.app_context():
        order = Order.query.get(order_id)
        assert order.status == 'processing'

def test_update_completed_order_status(client, init_database):
    """测试更新已完成订单的状态"""
    # 先创建一个订单并设置为已完成
    with client.application.app_context():
        product = Product.query.first()
        
    data = {
        'customer_name': '测试客户',
        'customer_phone': '13900139000',
        'items': [
            {
                'product_id': product.id,
                'quantity': 2,
                'price': 99.99
            }
        ],
        'remark': '测试订单'
    }
    
    response = client.post('/api/order', json=data)
    order_id = response.get_json()['data']['order_id']
    
    # 先将订单设置为已完成
    client.post(f'/api/order/{order_id}/status', json={'status': 'completed'})
    
    # 尝试更新已完成订单的状态
    response = client.post(f'/api/order/{order_id}/status', json={'status': 'processing'})
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['code'] == 400
    assert '已完成' in json_data['message'] 