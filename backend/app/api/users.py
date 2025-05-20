from flask import Blueprint, request, jsonify
from app import db
from app.models import User, VIPLevel, UserActivityLog # Import User, VIPLevel, and UserActivityLog
from app.schemas import UserSchema, SubAccountCreateSchema, UserInfoSchema, SubAccountUpdateSchema, UserActivityLogSchema # Import UserSchema, SubAccountCreateSchema, UserInfoSchema, SubAccountUpdateSchema, and UserActivityLogSchema
from app.decorators import token_required, permission_required
from app.utils import log_activity # Import the logger

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/users/me', methods=['GET'])
@token_required
def get_current_user_profile(current_user):
    # Use UserInfoSchema for a more controlled output of user information
    schema = UserInfoSchema()
    return jsonify(schema.dump(current_user)), 200

@users_bp.route('/users/me', methods=['PUT'])
@token_required
def update_current_user_profile(current_user):
    # For Phase 1, let's assume only email and phone_number can be updated by the user themselves.
    # Password update should be a separate endpoint (e.g., /auth/change-password)
    # Role, status, vip_level should be managed by admin or specific processes.
    schema = UserSchema(only=("email", "phone_number"), partial=True)
    try:
        data = schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors", "errors": e.args[0]}), 400

    if 'email' in data and data['email'] != current_user.email and User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already exists"}), 409
    
    # Add similar check for phone_number if it needs to be unique and is provided
    if 'phone_number' in data and data['phone_number'] != current_user.phone_number and data['phone_number'] and User.query.filter_by(phone_number=data['phone_number']).first():
        return jsonify({"message": "Phone number already exists"}), 409

    for key, value in data.items():
        setattr(current_user, key, value)
    
    db.session.commit()
    user_info_schema = UserInfoSchema()
    return jsonify({"message": "Profile updated successfully", "user": user_info_schema.dump(current_user)}), 200


@users_bp.route('/users/me/sub-accounts', methods=['POST'])
@token_required
# @permission_required(allowed_roles=['parent_user']) # More specific role check could be added
def create_sub_account(current_user):
    # Check if the current user is a parent_user (or has rights to create sub-accounts)
    if current_user.role not in ['parent_user', 'super_admin']: # super_admin can also create for testing/management
        return jsonify({"message": "Only parent users can create sub-accounts."}), 403

    # Check sub-account limit based on VIP level
    # For MVP, if not a VIP, maybe a default small limit (e.g., 1 or 0 without VIP)
    # If VIP, use vip_level.sub_account_limit
    limit = 0
    if current_user.vip_level:
        limit = current_user.vip_level.sub_account_limit
        if limit == -1: # Unlimited
            pass 
        elif len(current_user.sub_accounts.all()) >= limit:
             return jsonify({"message": f"Sub-account limit of {limit} reached for your VIP level."}), 403
    elif len(current_user.sub_accounts.all()) >= 1: # Default limit for non-VIP parent_user (e.g. 1)
        return jsonify({"message": "Sub-account limit reached. Upgrade to VIP for more."}), 403

    create_schema = SubAccountCreateSchema()
    try:
        data = create_schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for sub-account creation", "errors": e.args[0]}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Sub-account username already exists"}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Sub-account email already exists"}), 409

    new_sub_account = User(
        username=data['username'], 
        email=data['email'],
        parent_user_id=current_user.id,
        role='sub_account' # Explicitly set role
    )
    new_sub_account.set_password(data['password'])
    
    db.session.add(new_sub_account)
    # Commit here to get new_sub_account.id for logging, if log_activity commits separately.
    # Or pass new_sub_account data to log_activity before commit if log_activity doesn't commit.
    db.session.commit() 

    log_activity(
        action="create_sub_account", 
        user_id=current_user.id, 
        target_user_id=new_sub_account.id, 
        details={"sub_account_username": new_sub_account.username, "sub_account_email": new_sub_account.email}
    )
    # If log_activity doesn't commit, main commit here: db.session.commit()

    user_info_schema = UserInfoSchema()
    return jsonify({"message": "Sub-account created successfully", "sub_account": user_info_schema.dump(new_sub_account)}), 201

@users_bp.route('/users/me/sub-accounts', methods=['GET'])
@token_required
def get_sub_accounts(current_user):
    if current_user.role not in ['parent_user', 'super_admin']:
        return jsonify({"message": "Access denied."}), 403
    
    sub_accounts = current_user.sub_accounts.all()
    schema = UserInfoSchema(many=True)
    return jsonify(schema.dump(sub_accounts)), 200

@users_bp.route('/users/me/sub-accounts/<int:sub_account_id>', methods=['GET'])
@token_required
def get_sub_account_detail(current_user, sub_account_id):
    sub_account = User.query.filter_by(id=sub_account_id, parent_user_id=current_user.id).first_or_404(
        description="Sub-account not found or not associated with this parent account."
    )
    # Ensure the fetched user is indeed a sub-account (though parent_user_id check largely covers this)
    if sub_account.role != 'sub_account':
        return jsonify({"message": "Specified user is not a sub-account."}), 403
        
    schema = UserInfoSchema()
    return jsonify(schema.dump(sub_account)), 200

@users_bp.route('/users/me/sub-accounts/<int:sub_account_id>', methods=['PUT'])
@token_required
def update_sub_account(current_user, sub_account_id):
    sub_account = User.query.filter_by(id=sub_account_id, parent_user_id=current_user.id).first_or_404(
        description="Sub-account not found or not associated with this parent account."
    )
    if sub_account.role != 'sub_account':
        return jsonify({"message": "Cannot update: Specified user is not a sub-account."}), 403

    update_schema = SubAccountUpdateSchema()
    try:
        data = update_schema.load(request.json, partial=True)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors for sub-account update", "errors": e.args[0]}), 400

    if not data:
        return jsonify({"message": "No update data provided"}), 400

    updated_fields = {}
    if 'password' in data and data['password']:
        sub_account.set_password(data['password'])
        updated_fields['password_changed'] = True # Or hash of new password for audit, but be careful
    elif 'password' in data and data['password'] is None:
        # Disallowing clearing password for sub-account by parent for now.
        # A sub-account should always have a password set by parent.
        return jsonify({"message": "Password cannot be empty for a sub-account."}), 400
        
    # Add other updatable fields here if SubAccountUpdateSchema is expanded (e.g., status, email)
    # e.g., if 'email' in data and data['email'] != sub_account.email:
    #     if User.query.filter(User.email == data['email'], User.id != sub_account.id).first():
    #         return jsonify({"message": "Email already in use."}), 409
    #     sub_account.email = data['email']

    # db.session.commit() # Commit before logging if log_activity commits, or after if not.
    # For now, log_activity commits. So commit main changes first.
    db.session.commit()

    if updated_fields: # Log only if something was actually changed
        log_activity(
            action="update_sub_account",
            user_id=current_user.id,
            target_user_id=sub_account.id,
            details=updated_fields
        )

    user_info_schema = UserInfoSchema()
    return jsonify({"message": "Sub-account updated successfully.", "sub_account": user_info_schema.dump(sub_account)}), 200

@users_bp.route('/users/me/sub-accounts/<int:sub_account_id>', methods=['DELETE'])
@token_required
def delete_sub_account(current_user, sub_account_id):
    sub_account = User.query.filter_by(id=sub_account_id, parent_user_id=current_user.id).first_or_404(
        description="Sub-account not found or not associated with this parent account."
    )
    if sub_account.role != 'sub_account':
         return jsonify({"message": "Cannot delete: Specified user is not a sub-account."}), 403

    # What to do with data associated with the sub-account? For now, just delete the user record.
    # The design doc doesn't specify cascading deletes or re-attribution of data.
    # Mark as inactive or truly delete?
    # For now, we will delete the user. Consider soft delete (changing status) for production.
    
    # If there are related entities that have FK constraints like ON DELETE RESTRICT, this will fail.
    # Need to handle deletion of related data or set FKs to ON DELETE SET NULL / CASCADE appropriately.
    # E.g., UserFeatureTrial, SubAccountFeaturePermission, UserActivityLog entries for this sub-account.
    # For MVP, direct delete, assuming simple FKs or manual cleanup later.
    
    sub_account_details_for_log = {
        "deleted_sub_account_username": sub_account.username,
        "deleted_sub_account_email": sub_account.email,
        "deleted_sub_account_id": sub_account.id
    }

    db.session.delete(sub_account)
    # db.session.commit() # Commit before logging if log_activity commits.
    db.session.commit()

    log_activity(
        action="delete_sub_account",
        user_id=current_user.id,
        # target_user_id is tricky here as the user is deleted. Log its ID in details.
        details=sub_account_details_for_log 
    )
    
    return jsonify({"message": "Sub-account deleted successfully."}), 200

@users_bp.route('/users/me/sub-accounts/<int:sub_account_id>/activity-logs', methods=['GET'])
@token_required
def get_sub_account_activity_logs(current_user, sub_account_id):
    # First, verify the sub_account_id belongs to the current_user (is their sub-account)
    sub_account = User.query.filter_by(id=sub_account_id, parent_user_id=current_user.id, role='sub_account').first_or_404(
        description="Sub-account not found or not associated with this parent account."
    )

    # Fetch logs where the sub_account is the actor (user_id = sub_account.id)
    # Or, fetch logs where sub_account is the target (target_user_id = sub_account.id) - e.g. parent changed their password
    # Design doc says "查看子账号活动日志", implying logs generated BY the sub-account.
    # For a more complete view, one might combine logs where sub_account is actor or target (if parent performs action on them).
    # Let's start with logs generated BY the sub-account itself.

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)

    logs_query = UserActivityLog.query.filter_by(user_id=sub_account.id)
    logs_pagination = logs_query.order_by(UserActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    logs = logs_pagination.items

    schema = UserActivityLogSchema(many=True)
    return jsonify({
        "logs": schema.dump(logs),
        "total_pages": logs_pagination.pages,
        "current_page": logs_pagination.page,
        "total_logs": logs_pagination.total
    }), 200

# TODO (Phase 1/2): GET /users/me/sub-accounts/{sub_account_id}/activity-logs 