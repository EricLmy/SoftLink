from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError, fields
from app import db
from app.models import DynamicMenuItem, Feature, Permission, VIPLevel, User, Feedback
from app.schemas import DynamicMenuItemSchema, FeatureSchema, AdminFeatureCreateSchema, AdminFeatureUpdateSchema, AdminUserVIPUpdateSchema, UserInfoSchema, AdminUserUpdateSchema, FeedbackSchema, AdminFeedbackUpdateSchema
from app.decorators import permission_required, token_required
from app.utils import parse_query_param
from datetime import datetime

admin_bp = Blueprint('admin_bp', __name__)

# Schemas for loading data for admin operations
class AdminDynamicMenuItemCreateSchema(DynamicMenuItemSchema):
    class Meta(DynamicMenuItemSchema.Meta):
        # Fields required for creation, adjust as necessary
        fields = ("name", "url", "icon", "parent_id", "feature_identifier", "required_permission_name", "order", "is_enabled")
        # Make parent_id, feature_identifier, required_permission_name optional on load for creation
        dump_only = DynamicMenuItemSchema.Meta.dump_only + ("id", "children", "feature")

    # Override to make fields not strictly required for initial creation payload if they can be null
    parent_id = fields.Integer(allow_none=True, load_default=None)
    feature_identifier = fields.String(allow_none=True, load_default=None)
    required_permission_name = fields.String(allow_none=True, load_default=None)
    icon = fields.String(allow_none=True, load_default=None)
    order = fields.Integer(load_default=0)
    is_enabled = fields.Boolean(load_default=True)

@admin_bp.route('/admin/dynamic-menu-items', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer']) # Example: Allow developers too
def get_dynamic_menu_items(current_user):
    # For simplicity, fetching all items. Add pagination for many items.
    # Also, consider fetching in a way that allows easy reconstruction of hierarchy on client, or return nested.
    items = DynamicMenuItem.query.order_by(DynamicMenuItem.parent_id.asc(), DynamicMenuItem.order.asc()).all()
    schema = DynamicMenuItemSchema(many=True)
    return jsonify(schema.dump(items)), 200

@admin_bp.route('/admin/dynamic-menu-items', methods=['POST'])
@permission_required(allowed_roles=['super_admin']) # Only super_admin can create
def create_dynamic_menu_item(current_user):
    create_schema = AdminDynamicMenuItemCreateSchema()
    try:
        data = create_schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for menu item creation", "errors": e.args[0]}), 400

    # 确保data是字典类型，而不是DynamicMenuItem对象
    if isinstance(data, dict):
        # Validate feature_identifier if provided
        feature_identifier = data.get('feature_identifier')
        if feature_identifier and not Feature.query.filter_by(identifier=feature_identifier).first():
            return jsonify({"message": f"Feature with identifier {feature_identifier} not found."}), 400
        
        # Validate required_permission_name if provided
        required_permission_name = data.get('required_permission_name')
        if required_permission_name and not Permission.query.filter_by(name=required_permission_name).first():
            return jsonify({"message": f"Permission with name {required_permission_name} not found."}), 400

        new_item = DynamicMenuItem(**data)
    else:
        # 如果data是对象，转换为字典
        data_dict = {}
        for key in ["name", "url", "icon", "parent_id", "feature_identifier", "required_permission_name", "order", "is_enabled"]:
            if hasattr(data, key):
                data_dict[key] = getattr(data, key)
        
        # 验证字段
        if data_dict.get('feature_identifier') and not Feature.query.filter_by(identifier=data_dict['feature_identifier']).first():
            return jsonify({"message": f"Feature with identifier {data_dict['feature_identifier']} not found."}), 400
        
        if data_dict.get('required_permission_name') and not Permission.query.filter_by(name=data_dict['required_permission_name']).first():
            return jsonify({"message": f"Permission with name {data_dict['required_permission_name']} not found."}), 400
        
        new_item = DynamicMenuItem(**data_dict)

    db.session.add(new_item)
    db.session.commit()

    result_schema = DynamicMenuItemSchema()
    return jsonify({"message": "Dynamic menu item created successfully", "item": result_schema.dump(new_item)}), 201

@admin_bp.route('/admin/dynamic-menu-items/<int:item_id>', methods=['PUT'])
@permission_required(allowed_roles=['super_admin'])
def update_dynamic_menu_item(current_user, item_id):
    item = DynamicMenuItem.query.get_or_404(item_id)
    # Use the same schema as create, but allow partial updates
    update_schema = AdminDynamicMenuItemCreateSchema() 
    try:
        data = update_schema.load(request.json, partial=True)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for menu item update", "errors": e.args[0]}), 400

    if not data:
        return jsonify({"message": "No update data provided"}), 400

    # 确保data是字典类型
    data_dict = data if isinstance(data, dict) else {k: getattr(data, k) for k in data.__dict__ if not k.startswith('_')}

    # Validate feature_identifier if provided and changed
    if data_dict.get('feature_identifier') and data_dict['feature_identifier'] != item.feature_identifier and not Feature.query.filter_by(identifier=data_dict['feature_identifier']).first():
        return jsonify({"message": f"Feature with identifier {data_dict['feature_identifier']} not found."}), 400
    
    # Validate required_permission_name if provided and changed
    if data_dict.get('required_permission_name') and data_dict['required_permission_name'] != item.required_permission_name and not Permission.query.filter_by(name=data_dict['required_permission_name']).first():
        return jsonify({"message": f"Permission with name {data_dict['required_permission_name']} not found."}), 400
    
    # Prevent creating circular dependencies with parent_id
    if 'parent_id' in data_dict and data_dict['parent_id'] is not None:
        if data_dict['parent_id'] == item.id:
            return jsonify({"message": "Menu item cannot be its own parent."}), 400
        # Further check to prevent making a child of one of its own descendants (more complex)
        # For now, basic self-parenting check.

    for key, value in data_dict.items():
        setattr(item, key, value)
    
    db.session.commit()
    result_schema = DynamicMenuItemSchema()
    return jsonify({"message": "Dynamic menu item updated successfully", "item": result_schema.dump(item)}), 200

@admin_bp.route('/admin/dynamic-menu-items/<int:item_id>', methods=['DELETE'])
@permission_required(allowed_roles=['super_admin'])
def delete_dynamic_menu_item(current_user, item_id):
    item = DynamicMenuItem.query.get_or_404(item_id)

    # Check if this item is a parent to any other items
    if DynamicMenuItem.query.filter_by(parent_id=item.id).first():
        return jsonify({"message": "Cannot delete menu item: it has child items. Delete children first or reassign them."}), 400

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Dynamic menu item deleted successfully"}), 200

@admin_bp.route('/admin/features', methods=['POST'])
@permission_required(allowed_roles=['super_admin'])
def create_feature(current_user):
    create_schema = AdminFeatureCreateSchema()
    try:
        data = create_schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for feature creation", "errors": e.args[0]}), 400

    # 确保data是字典类型，而不是Feature对象
    if isinstance(data, dict):
        identifier = data.get('identifier')
        if identifier and Feature.query.filter_by(identifier=identifier).first():
            return jsonify({"message": f"Feature with identifier {identifier} already exists."}), 409
        
        name = data.get('name')
        if name and Feature.query.filter_by(name=name).first():
            return jsonify({"message": f"Feature with name {name} already exists."}), 409

        # Validate min_vip_level_required_id if provided
        min_vip_level_required_id = data.get('min_vip_level_required_id')
        if min_vip_level_required_id and not VIPLevel.query.get(min_vip_level_required_id):
            return jsonify({"message": f"VIPLevel with id {min_vip_level_required_id} not found."}), 400

        new_feature = Feature(**data)
    else:
        # 如果data是对象，转换为字典
        data_dict = {}
        for key in ["name", "identifier", "description", "base_url", "icon", "is_core_feature", "trial_days", "min_vip_level_required_id", "is_enabled"]:
            if hasattr(data, key):
                data_dict[key] = getattr(data, key)
        
        # 验证字段
        if Feature.query.filter_by(identifier=data_dict.get('identifier', '')).first():
            return jsonify({"message": f"Feature with identifier {data_dict.get('identifier')} already exists."}), 409
        
        if Feature.query.filter_by(name=data_dict.get('name', '')).first():
            return jsonify({"message": f"Feature with name {data_dict.get('name')} already exists."}), 409
        
        if data_dict.get('min_vip_level_required_id') and not VIPLevel.query.get(data_dict.get('min_vip_level_required_id')):
            return jsonify({"message": f"VIPLevel with id {data_dict.get('min_vip_level_required_id')} not found."}), 400
        
        new_feature = Feature(**data_dict)
    
    db.session.add(new_feature)
    db.session.commit()

    result_schema = FeatureSchema()
    return jsonify({"message": "Feature created successfully", "feature": result_schema.dump(new_feature)}), 201

@admin_bp.route('/admin/features/<int:feature_id>', methods=['PUT'])
@permission_required(allowed_roles=['super_admin'])
def update_feature(current_user, feature_id):
    feature = Feature.query.get_or_404(feature_id)
    update_schema = AdminFeatureUpdateSchema()

    try:
        data = update_schema.load(request.json, partial=True)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for feature update", "errors": e.args[0]}), 400

    # 确保data是字典类型
    data_dict = data if isinstance(data, dict) else {k: getattr(data, k) for k in data.__dict__ if not k.startswith('_')}

    # Check for name conflict if name is being changed
    if 'name' in data_dict and data_dict['name'] != feature.name and Feature.query.filter_by(name=data_dict['name']).first():
        return jsonify({"message": f"Feature with name {data_dict['name']} already exists."}), 409
    
    # Validate min_vip_level_required_id if provided and changed
    if data_dict.get('min_vip_level_required_id') and data_dict['min_vip_level_required_id'] != feature.min_vip_level_required_id and not VIPLevel.query.get(data_dict['min_vip_level_required_id']):
        return jsonify({"message": f"VIPLevel with id {data_dict['min_vip_level_required_id']} not found."}), 400

    for key, value in data_dict.items():
        setattr(feature, key, value)
    
    db.session.commit()

    result_schema = FeatureSchema()
    return jsonify({"message": "Feature updated successfully", "feature": result_schema.dump(feature)}), 200

@admin_bp.route('/admin/features', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer'])
def get_features(current_user):
    features = Feature.query.all()
    schema = FeatureSchema(many=True)
    return jsonify(schema.dump(features)), 200

@admin_bp.route('/admin/users/<int:user_id>/vip', methods=['PUT'])
@permission_required(allowed_roles=['super_admin'])
def update_user_vip_status(current_admin, user_id):
    user = User.query.get_or_404(user_id)
    schema = AdminUserVIPUpdateSchema()

    try:
        data = schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for VIP update", "errors": e.args[0]}), 400

    vip_level = VIPLevel.query.get(data['vip_level_id'])
    if not vip_level:
        return jsonify({"message": f"VIPLevel with id {data['vip_level_id']} not found."}), 404

    try:
        # Attempt to parse the date string. More robust parsing might be needed.
        expiry_date = datetime.strptime(data['vip_expiry_date_str'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            expiry_date = datetime.strptime(data['vip_expiry_date_str'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid vip_expiry_date_str format. Use YYYY-MM-DD HH:MM:SS or YYYY-MM-DD."}), 400

    user.vip_level_id = vip_level.id
    user.vip_level = vip_level # Explicitly set relationship if needed by ORM state
    user.vip_expiry_date = expiry_date
    
    # Potentially create/update a Subscription record as well for consistency, though this is a manual override.
    # For MVP, direct User field update is simpler.
    # sub = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.end_date.desc()).first()
    # if sub and sub.status == 'active':
    #     sub.status = 'upgraded' # or some other status
    # new_sub = Subscription(user_id=user.id, vip_level_id=vip_level.id, start_date=datetime.utcnow(), end_date=expiry_date, status='active', payment_type='manual_admin')
    # db.session.add(new_sub)

    db.session.commit()

    user_info_schema = UserInfoSchema()
    return jsonify({"message": f"User {user.username}'s VIP status updated successfully.", "user": user_info_schema.dump(user)}), 200

@admin_bp.route('/admin/users', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer']) # Assuming developers might also need to list users
def get_all_users(current_admin):
    # Add pagination in a real application
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    users_query = User.query
    # Example simple filter by username, extend as needed
    username_filter = request.args.get('username')
    if username_filter:
        users_query = users_query.filter(User.username.ilike(f'%{username_filter}%'))
    
    users_pagination = users_query.paginate(page=page, per_page=per_page, error_out=False)
    users = users_pagination.items
    
    schema = UserInfoSchema(many=True) # Use UserInfoSchema for concise output
    return jsonify({
        "users": schema.dump(users),
        "total_pages": users_pagination.pages,
        "current_page": users_pagination.page,
        "total_users": users_pagination.total
    }), 200

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer'])
def get_user_by_id_admin(current_admin, user_id):
    user = User.query.get_or_404(user_id)
    schema = UserInfoSchema() # Or a more detailed admin-specific user schema if needed
    return jsonify(schema.dump(user)), 200

@admin_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@permission_required(allowed_roles=['super_admin'])
def update_user_by_admin(current_admin, user_id):
    user = User.query.get_or_404(user_id)
    
    schema = AdminUserUpdateSchema()
    try:
        data = schema.load(request.json, partial=True)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for user update", "errors": e.args[0]}), 400

    if not data:
        return jsonify({"message": "No update data provided"}), 400

    # Prevent admin from accidentally de-admining the last super_admin or themselves if not careful
    if user.role == 'super_admin' and User.query.filter_by(role='super_admin').count() == 1 and data.get('role') and data.get('role') != 'super_admin':
        return jsonify({"message": "Cannot change the role of the last super_admin."}), 403
    
    # Prevent changing own role if it's the current user
    if user.id == current_admin.id and data.get('role') and data.get('role') != current_admin.role:
        return jsonify({"message": "Super admin cannot change their own role directly via this endpoint."}), 403
        
    if data.get('username') and data['username'] != user.username and User.query.filter_by(username=data['username']).first():
        return jsonify({"message": f"Username '{data['username']}' already exists."}), 409
    
    if data.get('email') and data['email'] != user.email and User.query.filter_by(email=data['email']).first():
        return jsonify({"message": f"Email '{data['email']}' already exists."}), 409

    # Handle password update separately if included and allowed by schema (e.g., setting a temporary password)
    # For now, AdminUserUpdateSchema might not include password to prevent accidental direct setting.
    # If 'password' is in data and schema allows:
    #   user.password = data['password'] # This assumes the schema handles hashing or it's done here.

    for key, value in data.items():
        if key == 'password': # Explicitly skip password here, handle via a dedicated mechanism
            continue
        setattr(user, key, value)
    
    db.session.commit()
    user_info_schema = UserInfoSchema()
    return jsonify({"message": "User updated successfully", "user": user_info_schema.dump(user)}), 200

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@permission_required(allowed_roles=['super_admin'])
def delete_user_by_admin(current_admin, user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_admin.id:
        return jsonify({"message": "Super admin cannot delete themselves."}), 403
    
    if user.role == 'super_admin':
         # Optional: Check if this is the last super_admin
        if User.query.filter_by(role='super_admin').count() <= 1:
            return jsonify({"message": "Cannot delete the last super_admin account."}), 403

    # Add more checks if needed, e.g., handling related data (sub-accounts, logs, etc.)
    # For now, direct delete. Consider soft delete by changing status for production.
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user.username} (ID: {user_id}) deleted successfully."}), 200

@admin_bp.route('/admin/users', methods=['POST'])
@permission_required(allowed_roles=['super_admin'])
def create_user_by_admin(current_admin):
    # Assume a schema for admin creating users, might be different from user registration
    # For now, let's use a subset of UserInfoSchema or a new AdminUserCreateSchema
    # This schema should at least require username, email, password, and role.
    
    # Let's define a simple schema inline for now or ensure AdminUserCreateSchema exists
    # For demonstration, assuming AdminUserCreateSchema is similar to UserSchema but includes 'role'
    # and password handling.
    from app.schemas import UserSchema # UserSchema typically expects password

    # We need a specific schema for admin user creation that includes 'role'
    # and handles password appropriately (e.g. expects plain password and hashes it)
    # Let's assume UserSchema.load can take role and hashes password.
    # If not, a dedicated AdminUserCreateSchema is needed.
    
    # For now, let's assume a generic request.json structure for simplicity
    # In a real app, use a Marshmallow schema for validation.
    data = request.json
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": f"Username '{data['username']}' already exists."}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": f"Email '{data['email']}' already exists."}), 409
        
    valid_roles = [r.value for r in User.RoleEnum] # Get valid enum values
    if data['role'] not in valid_roles:
        return jsonify({"message": f"Invalid role: {data['role']}. Valid roles are: {valid_roles}"}), 400

    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data['role'],
        status=data.get('status', 'active') # Default to active if not provided
    )
    new_user.password = data['password'] # Assuming User model's password setter handles hashing
    
    # Handle parent_user_id if role is sub_account
    if data['role'] == 'sub_account':
        parent_id = data.get('parent_user_id')
        if not parent_id:
            return jsonify({"message": "parent_user_id is required for sub_account role."}), 400
        parent_user = User.query.get(parent_id)
        if not parent_user or parent_user.role != 'parent_user':
            return jsonify({"message": f"Invalid parent_user_id: {parent_id}. Must be a valid parent_user."}), 400
        new_user.parent_user_id = parent_id
        # Potentially check sub-account limits for the parent user here

    db.session.add(new_user)
    db.session.commit()
    
    user_info_schema = UserInfoSchema()
    return jsonify({"message": "User created successfully by admin.", "user": user_info_schema.dump(new_user)}), 201

@admin_bp.route('/admin/feedback', methods=['GET'])
@permission_required(allowed_roles=['super_admin'])
def get_all_feedback(current_admin):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Optionally filter by status or category
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')

    feedback_query = Feedback.query.order_by(Feedback.submitted_at.desc())

    if status_filter:
        feedback_query = feedback_query.filter(Feedback.status == status_filter)
    if category_filter:
        feedback_query = feedback_query.filter(Feedback.category.ilike(f'%{category_filter}%'))

    feedback_pagination = feedback_query.paginate(page=page, per_page=per_page, error_out=False)
    feedback_items = feedback_pagination.items
    
    schema = FeedbackSchema(many=True)
    feedback_data = schema.dump(feedback_items)
    
    # 注意：确保两个键都存在，都指向同一个列表
    return jsonify({
        "feedbacks": feedback_data,
        "feedback": feedback_data,
        "total_pages": feedback_pagination.pages,
        "current_page": feedback_pagination.page,
        "total_feedbacks": feedback_pagination.total
    }), 200

@admin_bp.route('/admin/feedback/<int:feedback_id>', methods=['PUT'])
@permission_required(allowed_roles=['super_admin'])
def update_feedback_status_by_admin(current_admin, feedback_id):
    feedback_item = Feedback.query.get_or_404(feedback_id)
    schema = AdminFeedbackUpdateSchema() # Defined in app.schemas

    try:
        data = schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for feedback update", "errors": e.args[0]}), 400

    feedback_item.status = data['status']
    feedback_item.resolver_id = current_admin.id # Log which admin resolved it
    if data['status'] in ['resolved', 'closed'] and not feedback_item.resolved_at:
        feedback_item.resolved_at = datetime.utcnow()
        
    db.session.commit()
    
    result_schema = FeedbackSchema()
    return jsonify({"message": "Feedback status updated successfully.", "feedback_item": result_schema.dump(feedback_item)}), 200

@admin_bp.route('/admin/dynamic-menu-items/<int:item_id>', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer'])
def get_dynamic_menu_item(current_user, item_id):
    item = DynamicMenuItem.query.get_or_404(item_id)
    schema = DynamicMenuItemSchema()
    return jsonify(schema.dump(item)), 200

@admin_bp.route('/admin/features/<int:feature_id>', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer'])
def get_feature(current_user, feature_id):
    feature = Feature.query.get_or_404(feature_id)
    schema = FeatureSchema()
    return jsonify(schema.dump(feature)), 200

@admin_bp.route('/admin/features/<int:feature_id>', methods=['DELETE'])
@permission_required(allowed_roles=['super_admin'])
def delete_feature(current_user, feature_id):
    feature = Feature.query.get_or_404(feature_id)
    
    # 检查是否有动态菜单项依赖此功能
    if DynamicMenuItem.query.filter_by(feature_identifier=feature.identifier).first():
        return jsonify({"message": f"Cannot delete feature: it is used by one or more menu items. Update or delete those items first."}), 400
    
    # 这里可以添加其他依赖检查，如用户试用记录等
    
    db.session.delete(feature)
    db.session.commit()
    return jsonify({"message": "Feature deleted successfully"}), 200

@admin_bp.route('/admin/feedbacks', methods=['GET'])
@permission_required(allowed_roles=['super_admin'])
def admin_get_feedbacks(current_admin):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Optionally filter by status or category
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    user_query = request.args.get('user_query')
    sort_by = request.args.get('sort_by', 'submitted_at')
    order = request.args.get('order', 'desc')

    # 构建查询
    feedback_query = Feedback.query
    
    # 应用过滤条件
    if status_filter:
        feedback_query = feedback_query.filter(Feedback.status == status_filter)
    if category_filter:
        feedback_query = feedback_query.filter(Feedback.category.ilike(f'%{category_filter}%'))
    
    if user_query:
        # 如果是搜索用户或内容
        feedback_query = feedback_query.join(User, Feedback.user_id == User.id, isouter=True)\
                    .filter((User.username.ilike(f'%{user_query}%')) | 
                            (User.email.ilike(f'%{user_query}%')) |
                            (Feedback.content.ilike(f'%{user_query}%')))
    
    # 应用排序
    if hasattr(Feedback, sort_by):
        if order == 'asc':
            feedback_query = feedback_query.order_by(getattr(Feedback, sort_by).asc())
        else:
            feedback_query = feedback_query.order_by(getattr(Feedback, sort_by).desc())
    else:
        # 默认按提交时间排序
        feedback_query = feedback_query.order_by(Feedback.submitted_at.desc())

    feedback_pagination = feedback_query.paginate(page=page, per_page=per_page, error_out=False)
    feedback_items = feedback_pagination.items
    
    schema = FeedbackSchema(many=True)
    feedback_data = schema.dump(feedback_items)
    
    return jsonify({
        "feedbacks": feedback_data,
        "total": feedback_pagination.total,
        "total_pages": feedback_pagination.pages,
        "current_page": feedback_pagination.page
    }), 200

@admin_bp.route('/admin/feedbacks/<int:feedback_id>/status', methods=['PUT'])
@permission_required(allowed_roles=['super_admin'])
def admin_update_feedback_status(current_admin, feedback_id):
    feedback_item = Feedback.query.get_or_404(feedback_id)
    schema = AdminFeedbackUpdateSchema()
    try:
        data = schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "验证错误", "errors": e.args[0]}), 400

    # 获取前端可能发送的解决备注
    resolution_notes = request.json.get('resolution_notes')
    
    feedback_item.status = data['status']
    
    # 如果提供了解决备注，更新它
    if resolution_notes:
        feedback_item.resolution_notes = resolution_notes
    
    if data['status'] in ['resolved', 'closed'] and not feedback_item.resolved_at:
        feedback_item.resolved_at = datetime.utcnow()
        feedback_item.resolver_id = current_admin.id
    
    # 如果状态从已解决/已关闭更改回其他状态，清除解决信息
    elif data['status'] not in ['resolved', 'closed']:
        feedback_item.resolved_at = None
        feedback_item.resolver_id = None
        
    db.session.commit()
    result_schema = FeedbackSchema()
    return jsonify({
        "message": "反馈状态更新成功", 
        "feedback": result_schema.dump(feedback_item)
    }), 200

@admin_bp.route('/admin/feedbacks/<int:feedback_id>', methods=['DELETE'])
@permission_required(allowed_roles=['super_admin'])
def admin_delete_feedback(current_admin, feedback_id):
    feedback_item = Feedback.query.get_or_404(feedback_id)
    
    # 执行删除操作
    db.session.delete(feedback_item)
    db.session.commit()
    
    return jsonify({
        "message": "反馈已成功删除",
        "id": feedback_id
    }), 200

# TODO (Phase 1 / Later): Implement PUT and DELETE for /admin/dynamic-menu-items/{item_id}
# TODO (Phase 1): Implement admin endpoint for viewing user feedback (GET /admin/feedback) - can be part of feedback_bp or here 