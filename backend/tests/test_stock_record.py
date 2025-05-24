import pytest
from app import create_app, db
from app.models.stock_record import StockRecord
from app.models.product import Product
from app.models.merchant import Merchant
from app.models.inventory import Inventory

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
        
        # 创建测试出入库记录
        stock_record = StockRecord(
            product_id=product.id,
            merchant_id=merchant.id,
            type='in',
            quantity=50,
            operator='测试操作员',
            batch_number='BATCH001',
            remark='测试入库'
        )
        db.session.add(stock_record)
        db.session.commit()
        
        yield
        db.session.remove()
        db.drop_all()

def test_get_stock_record_list(client, init_database):
    """测试获取出入库记录列表"""
    response = client.get('/api/stock-record')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert len(data['data']) > 0
    assert data['data'][0]['type'] == 'in'
    assert data['data'][0]['quantity'] == 50
    assert data['data'][0]['batch_number'] == 'BATCH001'

def test_create_stock_record_in(client, init_database):
    """测试创建入库记录"""
    with client.application.app_context():
        product = Product.query.first()
        initial_inventory = Inventory.query.filter_by(product_id=product.id).first()
        initial_quantity = initial_inventory.quantity
        
        response = client.post('/api/stock-record', json={
            'product_id': product.id,
            'type': 'in',
            'quantity': 30,
            'operator': '测试操作员',
            'batch_number': 'BATCH002',
            'remark': '测试入库'
        })
        
        assert response.status_code == 200
        assert response.get_json()['code'] == 0
        
        # 验证库存是否增加
        updated_inventory = Inventory.query.filter_by(product_id=product.id).first()
        assert updated_inventory.quantity == initial_quantity + 30

def test_create_stock_record_out(client, init_database):
    """测试创建出库记录"""
    with client.application.app_context():
        product = Product.query.first()
        initial_inventory = Inventory.query.filter_by(product_id=product.id).first()
        initial_quantity = initial_inventory.quantity
        
        response = client.post('/api/stock-record', json={
            'product_id': product.id,
            'type': 'out',
            'quantity': 20,
            'operator': '测试操作员',
            'batch_number': 'BATCH003',
            'remark': '测试出库'
        })
        
        assert response.status_code == 200
        assert response.get_json()['code'] == 0
        
        # 验证库存是否减少
        updated_inventory = Inventory.query.filter_by(product_id=product.id).first()
        assert updated_inventory.quantity == initial_quantity - 20

def test_create_stock_record_out_insufficient(client, init_database):
    """测试库存不足的出库记录"""
    with client.application.app_context():
        product = Product.query.first()
        initial_inventory = Inventory.query.filter_by(product_id=product.id).first()
        
        response = client.post('/api/stock-record', json={
            'product_id': product.id,
            'type': 'out',
            'quantity': initial_inventory.quantity + 1,
            'operator': '测试操作员',
            'batch_number': 'BATCH004',
            'remark': '测试出库'
        })
        
        assert response.status_code == 400
        assert response.get_json()['code'] == 400
        assert '库存不足' in response.get_json()['message']

def test_create_stock_record_invalid_product(client, init_database):
    """测试无效商品ID的出入库记录"""
    response = client.post('/api/stock-record', json={
        'product_id': 9999,
        'type': 'in',
        'quantity': 30,
        'operator': '测试操作员',
        'batch_number': 'BATCH005',
        'remark': '测试入库'
    })
    
    assert response.status_code == 404
    assert response.get_json()['code'] == 404
    assert '商品不存在' in response.get_json()['message']

def test_get_stock_record_detail(client, init_database):
    """测试获取出入库记录详情"""
    with client.application.app_context():
        record = StockRecord.query.first()
        response = client.get(f'/api/stock-record/{record.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert data['data']['type'] == 'in'
        assert data['data']['quantity'] == 50
        assert data['data']['batch_number'] == 'BATCH001'

def test_get_stock_record_detail_not_found(client, init_database):
    """测试获取不存在的出入库记录详情"""
    response = client.get('/api/stock-record/9999')
    assert response.status_code == 404
    assert response.get_json()['code'] == 404
    assert '记录不存在' in response.get_json()['message'] 