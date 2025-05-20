from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app
from . import db # 改为相对导入
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON, func
from sqlalchemy.orm import relationship
# from sqlalchemy.dialects.postgresql import JSONB  # 注释掉，不使用PostgreSQL的JSONB类型

class VIPLevel(db.Model):
    """VIP等级表"""
    __tablename__ = 'vip_levels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    sub_account_limit = db.Column(db.Integer, nullable=False, default=10) # Limit of sub-accounts for this level
    monthly_price = db.Column(db.Numeric(10, 2), nullable=False)
    quarterly_price = db.Column(db.Numeric(10, 2), nullable=True)
    annual_price = db.Column(db.Numeric(10, 2), nullable=True)
    lifetime_price = db.Column(db.Numeric(10, 2), nullable=True)
    description = db.Column(db.Text, nullable=True)
    permissions_config = db.Column(JSON, nullable=True) # Specific permissions for this level
    users = db.relationship('User', backref='vip_level', lazy='dynamic')

    def __repr__(self):
        return f'<VIPLevel {self.name}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.String(50), nullable=False, default='parent_user') # Enum values from design: 'parent_user', 'sub_account', 'super_admin', 'developer'
    status = db.Column(db.String(50), default='active') # Enum: 'active', 'inactive', 'suspended'
    
    vip_level_id = db.Column(db.Integer, db.ForeignKey('vip_levels.id'), nullable=True)
    vip_expiry_date = db.Column(db.DateTime, nullable=True)
    
    parent_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sub_accounts = db.relationship('User', backref=db.backref('parent_user', remote_side=[id]), lazy='dynamic')
    
    # max_sub_accounts will be dynamically calculated or managed by business logic as per doc
    # For now, we rely on vip_level.sub_account_limit

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)

    # Relationships for other tables as they are defined
    # activity_logs = db.relationship('UserActivityLog', foreign_keys=['UserActivityLog.user_id'], backref='user', lazy='dynamic')
    # feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    preferences = db.relationship('UserPreference', backref='user', uselist=False, lazy='joined')
    # api_keys = db.relationship('UserApiKey', backref='user', lazy='dynamic')
    # subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    # feature_trials = db.relationship('UserFeatureTrial', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vip_level_id = db.Column(db.Integer, db.ForeignKey('vip_levels.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False) # For lifetime, can be a far future date
    payment_type = db.Column(db.String(50)) # e.g., 'monthly', 'annual', 'lifetime'
    amount_paid = db.Column(db.Numeric(10, 2))
    transaction_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='active') # e.g., 'active', 'expired', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('subscriptions', lazy='dynamic'))
    vip_level_subscribed = db.relationship('VIPLevel', backref='subscribers')

    def __repr__(self):
        return f'<Subscription {self.id} for User {self.user_id}>'

class Feature(db.Model):
    __tablename__ = 'features'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    identifier = db.Column(db.String(100), unique=True, nullable=False, index=True) # For routing/permission control
    description = db.Column(db.Text, nullable=True)
    base_url = db.Column(db.String(255), nullable=True) # Base path for the feature/app
    icon = db.Column(db.String(100), nullable=True)
    is_core_feature = db.Column(db.Boolean, default=False)
    trial_days = db.Column(db.Integer, default=7)
    min_vip_level_required_id = db.Column(db.Integer, db.ForeignKey('vip_levels.id'), nullable=True)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    min_vip_level_required = db.relationship('VIPLevel')
    # Dynamic menu items can link to features
    # User feature trials will link to this

    def __repr__(self):
        return f'<Feature {self.name}>'

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True) # Nullable for anonymous feedback as per doc
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending') # 'pending', 'processing', 'resolved', 'closed'
    category = db.Column(db.String(100), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Admin/Developer who resolved it
    resolution_notes = db.Column(db.Text, nullable=True) # 添加解决备注字段

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('feedbacks', lazy='dynamic'))
    resolver = db.relationship('User', foreign_keys=[resolver_id])

    def __repr__(self):
        return f'<Feedback {self.id} by User {self.user_id}>'

class DynamicMenuItem(db.Model):
    __tablename__ = 'dynamic_menu_items'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('dynamic_menu_items.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(255), nullable=False) # Can be internal route or external link
    feature_identifier = db.Column(db.String(100), db.ForeignKey('features.identifier'), nullable=True)
    required_permission_name = db.Column(db.String(100), db.ForeignKey('permissions.name'), nullable=True) # Link to a Permission name
    order = db.Column(db.Integer, default=0)
    is_enabled = db.Column(db.Boolean, default=True)

    feature = db.relationship('Feature')
    # required_permission = db.relationship('Permission') # This relationship will be set up after Permission model
    children = db.relationship("DynamicMenuItem", backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<DynamicMenuItem {self.name}>'

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # e.g., 'create_sub_account', 'view_system_logs'
    description = db.Column(db.Text, nullable=True)

    # Relationship for DynamicMenuItem
    menu_items = db.relationship('DynamicMenuItem', backref='required_permission', lazy='dynamic')

    def __repr__(self):
        return f'<Permission {self.name}>'

# Association table for User Roles (implicitly via User.role) and Permissions
# Or, if we define explicit Role entity:
# class Role(db.Model): ...
# For now, using User.role string and mapping it to Permissions via RolePermission

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    # Using User.role string as part of the key assumes role names are stable
    # Alternatively, create a separate Role table and use role_id FK
    role_name = db.Column(db.String(50), primary_key=True) # Matches values in User.role
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)

    permission = db.relationship('Permission')

    def __repr__(self):
        return f'<RolePermission Role: {self.role_name}, Permission ID: {self.permission_id}>'

# Update User model relationships if necessary (e.g. for Feedback, Subscription)
# (Existing User model is above these new models in the file)

# TODO for Phase 1 related to models:
# - UserActivityLog (important for sub-account activity, but can be slightly deferred if complex)
# - SubAccountFeaturePermission (detailed sub-account feature control - might be more phase 2)
# - UserFeatureTrial (if trial mechanism is implemented in phase 1)

# For relationships in User model, uncomment and adjust foreign_keys if they were defined above:
# User.feedbacks = db.relationship('Feedback', foreign_keys=[Feedback.user_id], backref='submitter', lazy='dynamic')
# User.subscriptions = db.relationship('Subscription', backref='subscriber', lazy='dynamic')

# TODO: Define other models from Section 4 of the System Design Document as needed for Phase 1:
# - Subscription (for VIP basic)
# - Feature (for feature integration example and dynamic menu)
# - UserActivityLog (for sub-account logging, may be deferred slightly but good to have early)
# - Feedback (for user feedback system)
# - DynamicMenuItem (for dynamic menu)
# - SubAccountFeaturePermission (for sub-account permissions)
# - UserPreference (Phase 2, can be skipped for Phase 1 MVP)
# - UserApiKey (Phase 3, can be skipped for Phase 1 MVP)
# - Permission & RolePermission (Core for RBAC, though User.role is a start)
# - SystemConfig (Can be deferred if no immediate complex configs needed)
# - UserFeatureTrial (For feature trial mechanism)

# For Phase 1 MVP, User and VIPLevel are foundational.
# We will add other models iteratively. 

class UserFeatureTrial(db.Model):
    __tablename__ = 'user_feature_trials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id'), nullable=False, index=True)
    trial_start_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    trial_end_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='active') # e.g., 'active', 'expired'

    user = db.relationship('User', backref=db.backref('feature_trials', lazy='dynamic'))
    feature = db.relationship('Feature', backref=db.backref('trial_users', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'feature_id', name='uq_user_feature_trial'),)

    def __repr__(self):
        return f'<UserFeatureTrial User {self.user_id} for Feature {self.feature_id}>'

class UserActivityLog(db.Model):
    __tablename__ = 'user_activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True) # e.g., if admin modifies a user, or parent modifies sub-account
    ip_address = db.Column(db.String(45), nullable=True)
    action = db.Column(db.String(255), nullable=False) # e.g., 'login', 'create_sub_account', 'update_feature_x_settings'
    details = db.Column(JSON, nullable=True) # Store additional context as JSON
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to the user performing the action
    actor = db.relationship('User', foreign_keys=[user_id], backref=db.backref('performed_activities', lazy='dynamic'))
    # Relationship to the user being acted upon (if any)
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref=db.backref('related_activities', lazy='dynamic'))

    def __repr__(self):
        return f'<UserActivityLog {self.id} by User {self.user_id} - {self.action}>'

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    theme = db.Column(db.String(50), nullable=True, default='light') # e.g., 'light', 'dark', '科技蓝'
    language = db.Column(db.String(20), nullable=True, default='zh-CN') # e.g., 'zh-CN', 'en-US'
    notification_settings = db.Column(JSON, nullable=True) # e.g., {"email_updates": true, "system_alerts": true}
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserPreference for User {self.user_id}>'

# Update User model relationships if necessary (e.g. for Feedback, Subscription)
# ... (rest of the file) ... 