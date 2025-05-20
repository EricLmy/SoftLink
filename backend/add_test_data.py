"""
添加测试数据：VIP等级和功能模块
"""
from app import create_app, db
from app.models import VIPLevel, Feature
from decimal import Decimal
import traceback

app = create_app()

with app.app_context():
    try:
        print("1. 添加VIP等级数据")
        # 检查是否已有VIP等级
        existing_vip_levels = VIPLevel.query.all()
        if existing_vip_levels:
            print(f"已有{len(existing_vip_levels)}个VIP等级存在")
            vip_levels = existing_vip_levels
        else:
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
                    "monthly_price": Decimal("299.99"),  # 设置月付价格，实际上终身会员不需要月付
                    "quarterly_price": Decimal("799.99"),
                    "annual_price": Decimal("1999.99"),
                    "lifetime_price": Decimal("2999.99"),
                    "description": "终身VIP，支持创建无限子账户，享受所有功能，永久有效。",
                    "permissions_config": {"can_access_basic_features": True, "can_access_advanced_features": True, "can_access_premium_features": True, "unlimited_features": True}
                }
            ]
            
            # 添加测试VIP等级
            vip_levels = []
            for vip_level_data in test_vip_levels:
                new_vip_level = VIPLevel(**vip_level_data)
                db.session.add(new_vip_level)
                vip_levels.append(new_vip_level)
                print(f"添加VIP等级: {vip_level_data['name']}")
            
            # 提交VIP等级更改
            db.session.commit()
            print("成功添加测试VIP等级")
        
        print("\n2. 添加功能模块数据")
        # 检查是否已有功能模块
        existing_features = Feature.query.all()
        if existing_features:
            print(f"已有{len(existing_features)}个功能模块存在")
        
        # 定义测试功能模块
        test_features = [
            {
                "name": "在线库存管理",
                "identifier": "inventory_management",
                "description": "全面的库存追踪和管理系统，帮助您实时掌握库存状况，优化库存水平，减少滞销和缺货。支持多仓库管理、批次追踪和库存分析。",
                "base_url": "/feature/inventory",
                "icon": "/images/features/inventory.png",
                "is_core_feature": False,
                "trial_days": 7,
                "min_vip_level_required_id": vip_levels[0].id if len(vip_levels) >= 1 else None,
                "is_enabled": True
            },
            {
                "name": "客户关系管理",
                "identifier": "crm",
                "description": "强大的客户关系管理工具，帮助您管理客户信息、跟踪客户交互、分析客户行为，提升客户满意度和忠诚度。",
                "base_url": "/feature/crm",
                "icon": "/images/features/crm.png",
                "is_core_feature": False,
                "trial_days": 14,
                "min_vip_level_required_id": vip_levels[1].id if len(vip_levels) >= 2 else None,
                "is_enabled": True
            },
            {
                "name": "财务分析工具",
                "identifier": "financial_analysis",
                "description": "专业的财务分析工具，提供收入、支出、利润等关键财务指标的实时分析和可视化，帮助您做出明智的财务决策。",
                "base_url": "/feature/finance",
                "icon": "/images/features/finance.png",
                "is_core_feature": False,
                "trial_days": 7,
                "min_vip_level_required_id": vip_levels[2].id if len(vip_levels) >= 3 else None,
                "is_enabled": True
            },
            {
                "name": "人力资源管理",
                "identifier": "hr_management",
                "description": "全面的人力资源管理系统，帮助您管理员工信息、考勤、薪酬和绩效评估，提高人力资源管理效率。",
                "base_url": "/feature/hr",
                "icon": "/images/features/hr.png",
                "is_core_feature": False,
                "trial_days": 10,
                "min_vip_level_required_id": vip_levels[1].id if len(vip_levels) >= 2 else None,
                "is_enabled": True
            },
            {
                "name": "数据统计报表",
                "identifier": "data_reports",
                "description": "强大的数据分析和报表工具，自动生成各类业务报表，提供多维度数据分析，帮助您洞察业务趋势和关键指标。",
                "base_url": "/feature/reports",
                "icon": "/images/features/reports.png",
                "is_core_feature": True,  # 核心功能，所有用户可用
                "trial_days": 0,
                "min_vip_level_required_id": None,
                "is_enabled": True
            },
            {
                "name": "供应链管理",
                "identifier": "supply_chain",
                "description": "优化您的供应链流程，连接供应商、仓库和配送网络，提高供应链透明度和效率，降低运营成本。",
                "base_url": "/feature/supply",
                "icon": "/images/features/supply.png",
                "is_core_feature": False,
                "trial_days": 7,
                "min_vip_level_required_id": vip_levels[2].id if len(vip_levels) >= 3 else None,
                "is_enabled": True
            },
        ]
        
        # 添加测试功能模块
        added_count = 0
        for feature_data in test_features:
            # 检查是否已存在
            existing = Feature.query.filter_by(identifier=feature_data["identifier"]).first()
            if existing:
                print(f"功能模块 '{feature_data['name']}' 已存在，跳过")
                continue
            
            # 创建新功能模块
            new_feature = Feature(**feature_data)
            db.session.add(new_feature)
            print(f"添加功能模块: {feature_data['name']}")
            added_count += 1
        
        # 提交功能模块更改
        if added_count > 0:
            db.session.commit()
            print(f"成功添加{added_count}个测试功能模块")
        else:
            print("没有新功能模块被添加")
    
    except Exception as e:
        db.session.rollback()
        print(f"添加失败: {str(e)}")
        traceback.print_exc()

print("\n脚本执行完成") 