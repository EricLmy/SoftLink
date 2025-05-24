import pytest
from app import create_app, db
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.merchant import Merchant

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database(app):
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        
        # 创建测试商家
        merchant = Merchant(
            name='测试商家',
            email='test2@example.com',
            phone='13800138002',
            password='password123'
        )
        db.session.add(merchant)
        db.session.commit()
        
        # 创建测试商品
        product = Product(
            merchant_id=merchant.id,
            name='测试商品',
            sku='TEST001',
            unit='个',
            price=100
        )
        db.session.add(product)
        db.session.commit()
        
        # 创建测试库存记录
        inventory = Inventory(
            product_id=product.id,
            merchant_id=merchant.id,
            quantity=100,
            warning_line=20
        )
        db.session.add(inventory)
        db.session.commit()
        
        yield
        db.session.remove()
        db.drop_all()

def test_get_inventory_list(client, init_database):
    """测试获取库存列表"""
    response = client.get('/api/inventory/inventory')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert len(data['data']) > 0
    assert data['data'][0]['quantity'] == 100
    assert data['data'][0]['warning_line'] == 20

def test_stocktaking(client, init_database):
    """测试库存盘点功能"""
    with client.application.app_context():
        inventory = Inventory.query.first()
        response = client.post(f'/api/inventory/inventory/{inventory.id}/stocktaking', json={
            'quantity': 150
        })
        assert response.status_code == 200
        assert response.get_json()['code'] == 0
        updated_inventory = Inventory.query.get(inventory.id)
        assert updated_inventory.quantity == 150

def test_set_warning_line(client, init_database):
    """测试设置告警线"""
    with client.application.app_context():
        inventory = Inventory.query.first()
        response = client.post(f'/api/inventory/inventory/{inventory.id}/warning-line', json={
            'warning_line': 30
        })
        assert response.status_code == 200
        assert response.get_json()['code'] == 0
        updated_inventory = Inventory.query.get(inventory.id)
        assert updated_inventory.warning_line == 30

def test_invalid_stocktaking(client, init_database):
    """测试无效的库存盘点"""
    response = client.post('/api/inventory/inventory/999/stocktaking', json={
        'quantity': 150
    })
    assert response.status_code == 404
    assert response.get_json()['code'] == 404

def test_invalid_warning_line(client, init_database):
    """测试无效的告警线设置"""
    response = client.post('/api/inventory/inventory/999/warning-line', json={
        'warning_line': 30
    })
    assert response.status_code == 404
    assert response.get_json()['code'] == 404

def test_missing_quantity(client, init_database):
    """测试缺少数量参数的库存盘点"""
    with client.application.app_context():
        inventory = Inventory.query.first()
        response = client.post(f'/api/inventory/inventory/{inventory.id}/stocktaking', json={})
        assert response.status_code == 400
        assert response.get_json()['code'] == 400

def test_missing_warning_line(client, init_database):
    """测试缺少告警线参数的设置"""
    with client.application.app_context():
        inventory = Inventory.query.first()
        response = client.post(f'/api/inventory/inventory/{inventory.id}/warning-line', json={})
        assert response.status_code == 400
        assert response.get_json()['code'] == 400 