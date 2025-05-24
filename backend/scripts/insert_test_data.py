import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Product, Inventory, Merchant

app = create_app()
with app.app_context():
    try:
        # 创建测试商家
        merchant = Merchant(
            name='测试商家',
            email='test2@example.com',
            phone='13800138001',
            password='test123',
            status=1
        )
        db.session.add(merchant)
        db.session.commit()
        print(f"创建测试商家成功，ID: {merchant.id}")

        # 插入测试商品
        product = Product(
            merchant_id=merchant.id,
            name='测试商品A',
            sku='TEST001',
            unit='个',
            status=1
        )
        db.session.add(product)
        db.session.commit()
        print(f"创建测试商品成功，ID: {product.id}")

        # 插入库存记录
        inventory = Inventory(
            product_id=product.id,
            merchant_id=merchant.id,
            quantity=100,
            warning_line=20
        )
        db.session.add(inventory)
        db.session.commit()
        print(f"创建库存记录成功，ID: {inventory.id}，当前库存: {inventory.quantity}")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        db.session.rollback() 