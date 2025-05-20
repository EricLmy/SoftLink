from flask import Blueprint, jsonify, request
from app import db
from app.models import UserPreference
from app.schemas import UserPreferenceSchema, UserPreferenceUpdateSchema
from app.decorators import token_required
from app.utils import log_activity
from marshmallow import ValidationError

preferences_bp = Blueprint('preferences_bp', __name__)

@preferences_bp.route('/users/me/preferences', methods=['GET'])
@token_required
def get_user_preferences(current_user):
    """获取当前用户的偏好设置"""
    # 检查用户是否已有偏好设置记录
    preference = current_user.preferences
    
    # 如果没有偏好设置记录，则创建一个默认设置
    if not preference:
        preference = UserPreference(
            user_id=current_user.id,
            theme='light',  # 默认浅色主题
            language='zh-CN',  # 默认中文
            notification_settings={'email_updates': True, 'system_alerts': True}  # 默认通知设置
        )
        db.session.add(preference)
        db.session.commit()
    
    schema = UserPreferenceSchema()
    return jsonify(schema.dump(preference)), 200

@preferences_bp.route('/users/me/preferences', methods=['PUT'])
@token_required
def update_user_preferences(current_user):
    """更新当前用户的偏好设置"""
    if not request.json:
        return jsonify({'message': '请求数据无效，缺少JSON数据'}), 400
    
    # 验证请求数据
    schema = UserPreferenceUpdateSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as e:
        return jsonify({'message': '参数验证错误', 'errors': e.messages}), 400
    
    # 获取当前用户的偏好设置，如果不存在则创建
    preference = current_user.preferences
    if not preference:
        preference = UserPreference(user_id=current_user.id)
        db.session.add(preference)
    
    # 更新偏好设置
    if 'theme' in data:
        preference.theme = data['theme']
    if 'language' in data:
        preference.language = data['language']
    if 'notification_settings' in data:
        # 如果已有设置，我们只更新传入的键，而不是完全替换
        if preference.notification_settings:
            current_settings = preference.notification_settings.copy()
            current_settings.update(data['notification_settings'])
            preference.notification_settings = current_settings
        else:
            preference.notification_settings = data['notification_settings']
    
    # 保存更改
    db.session.commit()
    
    # 记录活动
    log_activity(
        action="update_preferences", 
        user_id=current_user.id, 
        details=data
    )
    
    # 返回更新后的偏好设置
    result_schema = UserPreferenceSchema()
    return jsonify({
        'message': '偏好设置已更新',
        'preferences': result_schema.dump(preference)
    }), 200 