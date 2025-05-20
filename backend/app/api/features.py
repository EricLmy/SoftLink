from flask import Blueprint, jsonify, request
from app import db
from app.models import DynamicMenuItem, Permission, RolePermission, Feature, User, UserFeatureTrial, VIPLevel
from app.schemas import DynamicMenuItemSchema, FeatureSchema, UserFeatureTrialSchema
from app.decorators import token_required
from sqlalchemy import or_
from datetime import datetime, timedelta

features_bp = Blueprint('features_bp', __name__)

@features_bp.route('/features/dynamic-menu', methods=['GET'])
@token_required
def get_dynamic_menu(current_user):
    # Fetch all enabled menu items that either:
    # 1. Have no specific permission required (publicly visible to logged-in users after feature enabled)
    # 2. Or the user's role has the required permission.
    
    # Get permissions associated with the current user's role
    user_permissions = db.session.query(Permission.name).join(RolePermission).filter(
        RolePermission.role_name == current_user.role
    ).all()
    user_permission_names = [p[0] for p in user_permissions]

    # Query for menu items
    # A menu item is visible if:
    # - It's enabled AND
    #   - It has no required_permission_name OR
    #   - Its required_permission_name is in the user_permission_names list
    
    # Fetch top-level menu items (parent_id is NULL)
    top_level_items_query = DynamicMenuItem.query.filter(
        DynamicMenuItem.is_enabled == True,
        DynamicMenuItem.parent_id.is_(None),
        or_(
            DynamicMenuItem.required_permission_name.is_(None),
            DynamicMenuItem.required_permission_name.in_(user_permission_names)
        )
    ).order_by(DynamicMenuItem.order.asc())
    
    top_level_items = top_level_items_query.all()

    # Helper function to recursively build menu structure with permission checks
    def build_menu_tree(menu_items):
        tree = []
        for item in menu_items:
            item_data = DynamicMenuItemSchema().dump(item)
            # Fetch children with the same permission logic
            children_query = DynamicMenuItem.query.filter(
                DynamicMenuItem.is_enabled == True,
                DynamicMenuItem.parent_id == item.id,
                 or_(
                    DynamicMenuItem.required_permission_name.is_(None),
                    DynamicMenuItem.required_permission_name.in_(user_permission_names)
                )
            ).order_by(DynamicMenuItem.order.asc())
            
            children = children_query.all()
            if children:
                item_data['children'] = build_menu_tree(children)
            else:
                item_data['children'] = [] # Ensure children is always an array
            tree.append(item_data)
        return tree

    menu_tree = build_menu_tree(top_level_items)
    return jsonify(menu_tree), 200

@features_bp.route('/features', methods=['GET'])
@token_required
def get_available_features(current_user):
    all_enabled_features = Feature.query.filter_by(is_enabled=True).all()
    processed_features = []

    user_vip_level = current_user.vip_level

    for feature in all_enabled_features:
        access_status = "restricted"
        trial_end_date_iso = None

        # 1. Core feature access
        if feature.is_core_feature:
            access_status = "full_access"
        else:
            # 2. VIP access check
            if user_vip_level and feature.min_vip_level_required:
                # Assuming VIPLevel.id implies rank or a direct comparison is suitable.
                # A more robust system might have a rank/power attribute on VIPLevel.
                if user_vip_level.id >= feature.min_vip_level_required.id: 
                    access_status = "full_access"
            
            # 3. Trial access check (only if not already full_access)
            if access_status != "full_access":
                trial = UserFeatureTrial.query.filter_by(
                    user_id=current_user.id, 
                    feature_id=feature.id
                ).first()

                if trial:
                    if trial.status == 'active' and trial.trial_end_at >= datetime.utcnow():
                        access_status = "trial_active"
                        trial_end_date_iso = trial.trial_end_at.isoformat()
                    else: # Trial expired or used
                        access_status = "trial_expired"
                elif feature.trial_days > 0:
                    access_status = "trial_available"
                else: # No trial available and no VIP access
                    access_status = "vip_required"
        
        feature_data = FeatureSchema().dump(feature)
        feature_data['user_access_status'] = access_status
        if trial_end_date_iso:
            feature_data['trial_end_at'] = trial_end_date_iso
        
        processed_features.append(feature_data)
        
    return jsonify(processed_features), 200

@features_bp.route('/features/<string:feature_identifier>/start-trial', methods=['POST'])
@token_required
def start_feature_trial(current_user, feature_identifier):
    feature = Feature.query.filter_by(identifier=feature_identifier, is_enabled=True).first()
    if not feature:
        return jsonify({"message": f"Feature '{feature_identifier}' not found or not enabled."}), 404

    if feature.is_core_feature:
        return jsonify({"message": "Core features do not require a trial."}), 400

    user_vip_level = current_user.vip_level
    if user_vip_level and feature.min_vip_level_required and user_vip_level.id >= feature.min_vip_level_required.id:
        return jsonify({"message": "You already have VIP access to this feature."}), 400

    if not feature.trial_days or feature.trial_days <= 0:
        return jsonify({"message": "This feature does not offer a trial period."}), 400

    existing_trial = UserFeatureTrial.query.filter_by(user_id=current_user.id, feature_id=feature.id).first()
    if existing_trial:
        if existing_trial.status == 'active' and existing_trial.trial_end_at >= datetime.utcnow():
            return jsonify({"message": "Trial is already active for this feature."}), 409
        else: # Trial used or expired
            return jsonify({"message": "Trial period for this feature has already been used or expired."}), 403
    
    trial_start_at = datetime.utcnow()
    trial_end_at = trial_start_at + timedelta(days=feature.trial_days)
    
    new_trial = UserFeatureTrial(
        user_id=current_user.id,
        feature_id=feature.id,
        trial_start_at=trial_start_at,
        trial_end_at=trial_end_at,
        status='active'
    )
    db.session.add(new_trial)
    db.session.commit()

    trial_schema = UserFeatureTrialSchema()
    return jsonify({"message": f"Trial started for feature '{feature.name}'.", "trial_info": trial_schema.dump(new_trial)}), 201 