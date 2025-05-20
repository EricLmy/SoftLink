from flask import Blueprint, request, jsonify
from app import db
from app.models import Feedback
from app.schemas import FeedbackSchema, FeedbackSubmitSchema, AdminFeedbackUpdateSchema
from app.decorators import optional_token_required, token_required, permission_required
from datetime import datetime

feedback_bp = Blueprint('feedback_bp', __name__)

@feedback_bp.route('/feedback', methods=['POST'])
@optional_token_required # Allows anonymous or authenticated feedback
def submit_feedback(current_user):
    schema = FeedbackSubmitSchema()
    try:
        data = schema.load(request.json)
    except Exception as e: # Marshmallow validation error
        return jsonify({"message": "Validation errors", "errors": e.args[0]}), 400

    new_feedback = Feedback(
        content=data['content'],
        category=data.get('category')
    )

    if current_user:
        new_feedback.user_id = current_user.id
    
    db.session.add(new_feedback)
    db.session.commit()

    feedback_schema = FeedbackSchema()
    return jsonify({"message": "Feedback submitted successfully", "feedback": feedback_schema.dump(new_feedback)}), 201

@feedback_bp.route('/admin/feedbacks', methods=['GET'])
@permission_required(allowed_roles=['super_admin', 'developer']) # Or a specific 'view_feedback' permission
def get_all_feedback_admin(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    user_query = request.args.get('user_query')
    sort_by = request.args.get('sort_by', 'submitted_at')
    order = request.args.get('order', 'desc')
    
    # 开始构建查询
    query = Feedback.query
    
    # 应用过滤条件
    if status_filter:
        query = query.filter(Feedback.status == status_filter)
    
    if category_filter:
        query = query.filter(Feedback.category.ilike(f'%{category_filter}%'))
    
    if user_query:
        # 这里需要根据实际的ORM关系调整，假设User模型有username和email字段
        from app.models import User
        query = query.join(User, Feedback.user_id == User.id)\
                    .filter((User.username.ilike(f'%{user_query}%')) | 
                            (User.email.ilike(f'%{user_query}%')) |
                            (Feedback.content.ilike(f'%{user_query}%')))
    
    # 应用排序
    if order == 'asc':
        query = query.order_by(getattr(Feedback, sort_by).asc())
    else:
        query = query.order_by(getattr(Feedback, sort_by).desc())
    
    # 分页
    feedback_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    feedbacks = feedback_pagination.items
    
    feedback_schema = FeedbackSchema(many=True)
    feedback_data = feedback_schema.dump(feedbacks)
    return jsonify({
        "feedbacks": feedback_data,
        "total": feedback_pagination.total,
        "total_pages": feedback_pagination.pages,
        "current_page": feedback_pagination.page
    }), 200

@feedback_bp.route('/admin/feedbacks/<int:feedback_id>/status', methods=['PUT'])
@permission_required(allowed_roles=['super_admin', 'developer'])
def update_feedback_status_admin(current_user, feedback_id):
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
        # 现在可以使用resolution_notes字段
        feedback_item.resolution_notes = resolution_notes
    
    if data['status'] in ['resolved', 'closed'] and not feedback_item.resolved_at:
        feedback_item.resolved_at = datetime.utcnow()
        feedback_item.resolver_id = current_user.id
    
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

@feedback_bp.route('/admin/feedbacks/<int:feedback_id>', methods=['DELETE'])
@permission_required(allowed_roles=['super_admin'])
def delete_feedback_admin(current_user, feedback_id):
    feedback_item = Feedback.query.get_or_404(feedback_id)
    
    # 执行删除操作
    db.session.delete(feedback_item)
    db.session.commit()
    
    return jsonify({
        "message": "反馈已成功删除",
        "id": feedback_id
    }), 200

# TODO: Implement admin endpoints for feedback management (GET, PUT) as per design doc (Phase 1: super_admin views feedback list)
# Example: GET /admin/feedback (requires admin rights)
# @feedback_bp.route('/admin/feedback', methods=['GET'])
# @token_required
# @permission_required('view_feedback_list') # Placeholder for permission check
# def get_all_feedback(current_user):
#     feedbacks = Feedback.query.order_by(Feedback.submitted_at.desc()).all()
#     feedback_schema = FeedbackSchema(many=True)
#     return jsonify(feedback_schema.dump(feedbacks)), 200 