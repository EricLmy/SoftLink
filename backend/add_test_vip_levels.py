"""
添加测试VIP等级数据
"""
from app import create_app, db
from app.models import VIPLevel
from decimal import Decimal

app = create_app()

with app.app_context():
    # 检查是否已有VIP等级
    existing_vip_levels = VIPLevel.query.all()
    if existing_vip_levels:
        print(f"已有{len(existing_vip_levels)}个VIP等级存在，将添加新的测试VIP等级")
    
    # 定义测试VIP等级
    test_vip_levels = [
        {
            "name": "VIP1",
            "sub_account_limit": 10,
            "monthly_price": Decimal("29.99"),
            "quarterly_price": Decimal("79.99"),
            "annual_price": Decimal("299.99"),
            "lifetime_price": None,
            "description": "基础VIP，支持创建最多10个子账户，享受基础功能。",
            "permissions_config": {"can_access_basic_features": True}
        },
        {
            "name": "VIP2",
            "sub_account_limit": 20,
            "monthly_price": Decimal("49.99"),
            "quarterly_price": Decimal("139.99"),
            "annual_price": Decimal("499.99"),
            "lifetime_price": None,
            "description": "进阶VIP，支持创建最多20个子账户，享受更多高级功能。",
            "permissions_config": {"can_access_basic_features": True, "can_access_advanced_features": True}
        },
        {
            "name": "VIP3",
            "sub_account_limit": 50,
            "monthly_price": Decimal("99.99"),
            "quarterly_price": Decimal("269.99"),
            "annual_price": Decimal("999.99"),
            "lifetime_price": None,
            "description": "专业VIP，支持创建最多50个子账户，享受全部高级功能。",
            "permissions_config": {"can_access_basic_features": True, "can_access_advanced_features": True, "can_access_premium_features": True}
        },
        {
            "name": "VIP4 - 终身",
            "sub_account_limit": -1,  # 无限制
            "monthly_price": None,
            "quarterly_price": None,
            "annual_price": None,
            "lifetime_price": Decimal("2999.99"),
            "description": "终身VIP，支持创建无限子账户，享受所有功能，永久有效。",
            "permissions_config": {"can_access_basic_features": True, "can_access_advanced_features": True, "can_access_premium_features": True, "unlimited_features": True}
        }
    ]
    
    # 添加测试VIP等级
    for vip_level_data in test_vip_levels:
        # 检查是否已存在
        existing = VIPLevel.query.filter_by(name=vip_level_data["name"]).first()
        if existing:
            print(f"VIP等级 '{vip_level_data['name']}' 已存在，跳过")
            continue
        
        # 创建新VIP等级
        new_vip_level = VIPLevel(**vip_level_data)
        db.session.add(new_vip_level)
        print(f"添加VIP等级: {vip_level_data['name']}")
    
    # 提交更改
    try:
        db.session.commit()
        print("成功添加测试VIP等级")
    except Exception as e:
        db.session.rollback()
        print(f"添加失败: {str(e)}")

print("脚本执行完成") 