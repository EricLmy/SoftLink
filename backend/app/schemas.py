from app import ma # Marshmallow instance from app/__init__.py
from .models import User, VIPLevel, Subscription, Feature, Feedback, DynamicMenuItem, Permission, RolePermission, UserFeatureTrial, UserActivityLog, UserPreference # Added UserPreference
from marshmallow import fields, validate

class VIPLevelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = VIPLevel
        load_instance = True
        include_fk = True # Include foreign keys in the schema
        exclude = ("users",) # Exclude back-reference to users to avoid recursion

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_relationships = True # Include relationships
        # Exclude password_hash from being dumped (output)
        # It should only be used for loading (input) during registration/password set if needed, but handled by set_password method.
        exclude = ("password_hash", "sub_accounts", "parent_user") # Exclude for now to keep it simple, can be added specifically where needed

    # Fields for loading (input) that are not directly part of the model or need specific validation
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6))
    email = fields.Email(required=True)
    username = fields.String(required=True, validate=validate.Length(min=3))
    
    # Control what is dumped (output)
    # Example: if you want to dump vip_level details alongside user
    vip_level = fields.Nested(VIPLevelSchema, only=["id", "name", "sub_account_limit"])
    # To dump parent_user_id only if it exists
    parent_user_id = fields.Integer(dump_only=True, allow_none=True)


# Schema for user registration
class UserRegisterSchema(ma.Schema):
    username = fields.String(required=True, validate=validate.Length(min=3))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))

# Schema for user login
class UserLoginSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


# Minimal User Info Schema for responses (e.g. after login)
class UserInfoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "status", "vip_level_id", "vip_expiry_date", "last_login_at")
    # You might want to nest some info like VIP level name
    vip_level_name = fields.Method("get_vip_level_name", dump_only=True)
    # 显式添加vip_level_id字段以确保它可被访问
    vip_level_id = fields.Integer(allow_none=True)

    def get_vip_level_name(self, obj):
        return obj.vip_level.name if obj.vip_level else None

class SubscriptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Subscription
        load_instance = True
        include_fk = True
    user = fields.Nested(UserInfoSchema, only=["id", "username"])
    vip_level_subscribed = fields.Nested(VIPLevelSchema, only=["id", "name"])

class FeatureSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Feature
        load_instance = True
        include_fk = True
        dump_only = () # Initialize dump_only for potential extension by subclasses
    min_vip_level_required = fields.Nested(VIPLevelSchema, only=["id", "name"])

class FeedbackSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Feedback
        load_instance = True
        include_fk = True
    user = fields.Nested(UserInfoSchema, only=["id", "username", "email"])
    resolver = fields.Nested(UserInfoSchema, only=["id", "username"])
    resolution_notes = fields.String(allow_none=True)

class PermissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Permission
        load_instance = True

class RolePermissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = RolePermission
        load_instance = True
        include_fk = True
    permission = fields.Nested(PermissionSchema)

class DynamicMenuItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DynamicMenuItem
        load_instance = True
        include_fk = True
        dump_only = () # Initialize dump_only for potential extension by subclasses
    
    feature = fields.Nested(FeatureSchema, only=["id", "identifier", "name"])
    # required_permission = fields.Nested(PermissionSchema, only=["name"]) # Corrected: use name from required_permission_name string
    children = fields.List(fields.Nested('self')) # For nested menus
    # To represent required_permission_name string directly
    required_permission_name = fields.String()

# Schema for submitting feedback
class FeedbackSubmitSchema(ma.Schema):
    content = fields.String(required=True, validate=validate.Length(min=2))
    category = fields.String(required=False, allow_none=True)
    # user_id will be taken from authenticated user or None for anonymous

# Schemas for Admin operations on Features
class AdminFeatureCreateSchema(FeatureSchema):
    class Meta(FeatureSchema.Meta):
        # Specify fields required/allowed for creation by admin
        fields = (
            "name", "identifier", "description", "base_url", "icon", 
            "is_core_feature", "trial_days", "min_vip_level_required_id", "is_enabled"
        )
        dump_only = FeatureSchema.Meta.dump_only + ("id", "created_at", "min_vip_level_required")

    # Add any specific validation or load_default for creation if needed
    name = fields.String(required=True)
    identifier = fields.String(required=True)
    is_core_feature = fields.Boolean(load_default=False)
    trial_days = fields.Integer(load_default=7)
    is_enabled = fields.Boolean(load_default=True)
    min_vip_level_required_id = fields.Integer(allow_none=True) # FK

class AdminFeatureUpdateSchema(FeatureSchema):
    class Meta(FeatureSchema.Meta):
        fields = (
            "name", "description", "base_url", "icon", 
            "is_core_feature", "trial_days", "min_vip_level_required_id", "is_enabled"
        )
        # Identifier should generally not be updatable after creation as it might be used in code/configs.
        # If it needs to be, careful consideration of impacts is required.
        dump_only = FeatureSchema.Meta.dump_only + ("id", "identifier", "created_at", "min_vip_level_required")

    # For updates, fields are typically optional
    name = fields.String(required=False)
    description = fields.String(required=False, allow_none=True)
    base_url = fields.String(required=False, allow_none=True)
    icon = fields.String(required=False, allow_none=True)
    is_core_feature = fields.Boolean(required=False)
    trial_days = fields.Integer(required=False)
    min_vip_level_required_id = fields.Integer(required=False, allow_none=True)
    is_enabled = fields.Boolean(required=False)

# Schema for creating a sub-account
class SubAccountCreateSchema(ma.Schema):
    username = fields.String(required=True, validate=validate.Length(min=3))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    # feature_permissions will be handled in a more advanced version (Phase 2 or later for MVP)
    # For Phase 1, sub-account is created, permissions can be a TODO or a very basic default.
    # feature_permissions = fields.List(fields.Nested(SubAccountFeaturePermissionSchema), required=False)

class AdminUserVIPUpdateSchema(ma.Schema):
    vip_level_id = fields.Integer(required=True, allow_none=False) # Must provide a VIPLevel ID
    # vip_expiry_date is tricky. For MVP admin update, maybe we simplify.
    # For lifetime VIPs, end_date might be far future. For others, it needs calculation.
    # Let's require a string for expiry_date for now, admin needs to input it correctly.
    vip_expiry_date_str = fields.String(required=True, allow_none=False)
    # Alternatively, could take a duration like "30d", "1y", etc., and calculate from now.

class AdminUserUpdateSchema(ma.Schema):
    # Fields an admin can update for any user
    username = fields.String(validate=validate.Length(min=3))
    email = fields.Email()
    phone_number = fields.String(allow_none=True) # Assuming phone can be cleared
    role = fields.String(validate=validate.OneOf(['parent_user', 'sub_account', 'super_admin', 'developer']))
    status = fields.String(validate=validate.OneOf(['active', 'inactive', 'suspended']))
    # Password changes should be rare for admin, and might need a separate flow or careful handling.
    # For now, not including direct password set by admin here.
    # vip_level_id and vip_expiry_date are handled by AdminUserVIPUpdateSchema and its dedicated endpoint.

class AdminFeedbackUpdateSchema(ma.Schema):
    status = fields.String(required=True, validate=validate.OneOf(['pending', 'processing', 'resolved', 'closed']))
    # Admin might also add a resolution note or assign a resolver, not included in this MVP schema for simplicity.

class UserFeatureTrialSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserFeatureTrial
        load_instance = True
        include_fk = True
    
    user = fields.Nested(UserInfoSchema, only=["id", "username"])
    feature = fields.Nested(FeatureSchema, only=["id", "identifier", "name"])

class SubAccountUpdateSchema(ma.Schema):
    # Parent user can update these for their sub-account
    # Username change might be disallowed or require care due to uniqueness.
    # email = fields.Email() # For now, let's assume email can be updated.
    # Password can be changed by parent for sub-account
    password = fields.String(validate=validate.Length(min=6), allow_none=True) # Allow clearing/setting password
    # status = fields.String(validate=validate.OneOf(['active', 'inactive'])) # Parent might enable/disable sub-account
    # feature_permissions would be part of a more advanced update (Phase 2)

    # For MVP Phase 1, let's focus on password update and maybe status if User model supports easy parent-controlled status for sub-accounts.
    # The User.status field is more general. Let's stick to password for now for simplicity in Phase 1.
    # If username/email update is allowed, ensure conflict checks are in place.

class UserActivityLogSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserActivityLog
        load_instance = True # Though unlikely to load activity logs from request body
        include_fk = True
        # For dumping, control fields to show
        fields = ("id", "user_id", "actor_username", "target_user_id", "target_username", "ip_address", "action", "details", "timestamp")
    
    # Add actor and target username for easier display
    actor_username = fields.Method("get_actor_username", dump_only=True)
    target_username = fields.Method("get_target_username", dump_only=True)

    def get_actor_username(self, obj):
        return obj.actor.username if obj.actor else None

    def get_target_username(self, obj):
        return obj.target_user.username if obj.target_user else None

class UserPreferenceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserPreference
        load_instance = True
        include_fk = True
    
    # Note: For notification_settings, we will directly use the JSON field
    # We can add additional validation or field-specific loading/dumping logic here if needed

class UserPreferenceUpdateSchema(ma.Schema):
    """Schema for updating user preferences"""
    theme = fields.String(required=False, validate=validate.OneOf(['light', 'dark', '科技蓝']))
    language = fields.String(required=False, validate=validate.OneOf(['zh-CN', 'en-US']))
    notification_settings = fields.Dict(required=False)  # Allow any JSON/Dict for notifications, validate in API logic
    # If we need stricter validation for notification_settings, we could define another schema for it

# TODO: Define other schemas as needed for Phase 1:
# - SubAccountCreationSchema (specific fields for creating sub-accounts)
# - Schemas for Admin operations on DynamicMenuItem, Features etc. (DynamicMenuItem create schema is in admin.py for now)