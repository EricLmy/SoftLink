from flask import request, current_app # Added current_app
from app import db
from app.models import UserActivityLog
from datetime import datetime

def log_activity(action: str, user_id: int, target_user_id: int = None, details: dict = None):
    """Helper function to log user activities."""
    # Check if we are in a request context for remote_addr
    ip_addr = None
    if request:
        ip_addr = request.remote_addr
    
    try:
        log_entry = UserActivityLog(
            user_id=user_id,
            target_user_id=target_user_id,
            ip_address=ip_addr, 
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit() # Commit immediately or batch commits?
                          # For immediate logging, commit is fine.
                          # If part of larger transaction, might not commit here.
    except Exception as e:
        # Use current_app.logger if available
        logger = current_app.logger if current_app else None
        if logger:
            logger.error(f"Failed to log activity '{action}' for user {user_id}: {e}")
        else:
            # Fallback print if no app logger (e.g., testing outside app context or script)
            print(f"Fallback: Failed to log activity '{action}' for user {user_id}: {e}")
        # It might be desirable to rollback the session if the logging commit itself fails,
        # but usually, logging failure shouldn't break the main operation.
        # Consider db.session.rollback() here if this commit is critical and isolated.

def parse_query_param(param_value, param_type=str, default=None):
    """
    解析和转换查询参数
    
    Args:
        param_value: 要解析的参数值
        param_type: 目标类型 (str, int, float, bool)
        default: 如果解析失败或者值为None时的默认值
    
    Returns:
        转换后的参数值或默认值
    """
    if param_value is None:
        return default
    
    try:
        if param_type == bool:
            # 处理布尔值，支持"true", "1", "yes"作为True，其他作为False
            if isinstance(param_value, str):
                return param_value.lower() in ('true', '1', 'yes', 'y')
            return bool(param_value)
        elif param_type == int:
            return int(param_value)
        elif param_type == float:
            return float(param_value)
        else:
            # 默认当作字符串
            return str(param_value)
    except (ValueError, TypeError):
        return default

# Example usage (would be in an API endpoint):
# from .utils import log_activity
# log_activity("user_login", user_id=user.id)
# log_activity("create_sub_account", user_id=parent_user.id, target_user_id=new_sub_account.id, details={"sub_account_username": new_sub_account.username}) 