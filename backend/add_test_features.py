"""
添加测试功能模块数据
在已有的VIP等级数据基础上，创建几个测试功能模块
"""
from app import create_app, db
from app.models import Feature, VIPLevel
import traceback

app = create_app()

with app.app_context():
    try:
        # 获取已有的VIP等级
        vip_levels = VIPLevel.query.all()
        
        if not vip_levels:
            print("错误：未找到VIP等级数据，请先创建VIP等级")
            exit(1)
        else:
            print(f"找到{len(vip_levels)}个VIP等级")
        
        # 检查是否已有功能模块
        existing_features = Feature.query.all()
        if existing_features:
            print(f"已有{len(existing_features)}个功能模块存在，将添加新的测试功能模块")
        
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
        
        # 提交更改
        if added_count > 0:
            db.session.commit()
            print(f"成功添加{added_count}个测试功能模块")
        else:
            print("没有新功能模块被添加")
    
    except Exception as e:
        db.session.rollback()
        print(f"添加失败: {str(e)}")
        traceback.print_exc()

print("脚本执行完成") 