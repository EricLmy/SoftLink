from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from app.models import VIPLevel, User, Subscription
from app.schemas import VIPLevelSchema, SubscriptionSchema
from app.decorators import token_required
from app import db
from app.utils import log_activity
import uuid

vip_bp = Blueprint('vip_bp', __name__)

@vip_bp.route('/vip/levels', methods=['GET'])
def get_vip_levels():
    levels = VIPLevel.query.order_by(VIPLevel.monthly_price.asc(), VIPLevel.id.asc()).all() # Example ordering
    schema = VIPLevelSchema(many=True)
    return jsonify(schema.dump(levels)), 200

@vip_bp.route('/vip/subscribe', methods=['POST'])
@token_required
def subscribe_vip(current_user):
    """
    用户订阅/升级VIP
    
    请求体参数:
    - vip_level_id: VIP等级ID
    - payment_type: 支付类型，可选值为 'monthly', 'quarterly', 'annual', 'lifetime'
    - payment_details: 支付详情 (可选，用于集成实际支付网关)
    """
    if not request.json:
        return jsonify({"message": "请求数据无效，缺少JSON数据"}), 400
    
    # 验证请求数据
    vip_level_id = request.json.get('vip_level_id')
    payment_type = request.json.get('payment_type')
    
    if not vip_level_id or not payment_type:
        return jsonify({"message": "缺少必要参数：vip_level_id 或 payment_type"}), 400
    
    # 验证支付类型
    if payment_type not in ['monthly', 'quarterly', 'annual', 'lifetime']:
        return jsonify({"message": "支付类型无效，可选值为：monthly, quarterly, annual, lifetime"}), 400
    
    # 验证VIP等级是否存在
    vip_level = VIPLevel.query.get(vip_level_id)
    if not vip_level:
        return jsonify({"message": "VIP等级不存在"}), 404
    
    # 计算价格和到期时间
    price = 0
    end_date = None
    
    if payment_type == 'monthly':
        price = vip_level.monthly_price
        end_date = datetime.utcnow() + timedelta(days=30)
    elif payment_type == 'quarterly':
        price = vip_level.quarterly_price
        end_date = datetime.utcnow() + timedelta(days=90)
    elif payment_type == 'annual':
        price = vip_level.annual_price
        end_date = datetime.utcnow() + timedelta(days=365)
    elif payment_type == 'lifetime':
        price = vip_level.lifetime_price
        # 对于终身会员，设置一个很远的未来日期
        end_date = datetime.utcnow() + timedelta(days=365*100)  # 100年后
    
    # 检查价格是否有效
    if price is None:
        return jsonify({"message": f"VIP等级 {vip_level.name} 不支持 {payment_type} 支付类型"}), 400
    
    # 创建交易ID (实际应用中应该由支付网关生成)
    transaction_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
    
    # TODO: 在此处集成实际支付网关
    # 现在仅模拟支付过程，默认支付成功
    
    # 创建新的订阅记录
    subscription = Subscription(
        user_id=current_user.id,
        vip_level_id=vip_level_id,
        start_date=datetime.utcnow(),
        end_date=end_date,
        payment_type=payment_type,
        amount_paid=price,
        transaction_id=transaction_id,
        status='active'
    )
    
    # 更新用户的VIP状态
    current_user.vip_level_id = vip_level_id
    current_user.vip_expiry_date = end_date
    
    # 保存到数据库
    db.session.add(subscription)
    db.session.commit()
    
    # 记录活动日志
    log_activity(
        action="vip_subscription",
        user_id=current_user.id,
        details={
            "vip_level": vip_level.name,
            "payment_type": payment_type,
            "amount_paid": float(price) if price else 0,
            "transaction_id": transaction_id,
            "expiry_date": end_date.isoformat() if end_date else None
        }
    )
    
    # 返回订阅信息
    subscription_schema = SubscriptionSchema()
    return jsonify({
        "message": f"已成功订阅 {vip_level.name}",
        "subscription": subscription_schema.dump(subscription)
    }), 201

@vip_bp.route('/users/me/subscription', methods=['GET'])
@token_required
def get_current_subscription(current_user):
    """获取当前用户的订阅信息"""
    # 查找用户最新的有效订阅
    subscription = Subscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Subscription.created_at.desc()).first()
    
    # 如果没有找到订阅记录
    if not subscription:
        return jsonify({
            "message": "当前没有有效的VIP订阅",
            "has_subscription": False
        }), 200
    
    # 返回订阅信息
    subscription_schema = SubscriptionSchema()
    return jsonify({
        "has_subscription": True,
        "subscription": subscription_schema.dump(subscription),
        "vip_level": subscription.vip_level_subscribed.name if subscription.vip_level_subscribed else None,
        "expiry_date": subscription.end_date.isoformat() if subscription.end_date else None,
        "days_remaining": (subscription.end_date - datetime.utcnow()).days if subscription.end_date else None
    }), 200

# 管理员接口: 取消用户订阅
@vip_bp.route('/admin/users/<int:user_id>/subscription/cancel', methods=['POST'])
@token_required
def admin_cancel_subscription(current_user, user_id):
    """管理员取消用户订阅"""
    # 检查当前用户是否有权限
    if current_user.role not in ['super_admin', 'developer']:
        return jsonify({"message": "权限不足"}), 403
    
    # 查找用户
    user = User.query.get_or_404(user_id)
    
    # 查找用户的有效订阅
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).order_by(Subscription.created_at.desc()).first()
    
    if not subscription:
        return jsonify({"message": "找不到该用户的有效订阅"}), 404
    
    # 取消订阅
    subscription.status = 'cancelled'
    user.vip_level_id = None
    user.vip_expiry_date = None
    
    db.session.commit()
    
    # 记录活动日志
    log_activity(
        action="admin_cancel_subscription",
        user_id=current_user.id,
        target_user_id=user_id,
        details={
            "cancelled_subscription_id": subscription.id,
            "vip_level": subscription.vip_level_subscribed.name if subscription.vip_level_subscribed else None
        }
    )
    
    return jsonify({"message": f"已取消用户 {user.username} 的订阅"}), 200 