from flask import Blueprint, request, g
from flask_restx import Api, Resource, fields
from app.models import Alert
from app.extensions import db
from app.decorators import login_required

alert_bp = Blueprint('alert', __name__)
alert_api = Api(alert_bp, title='告警管理', prefix='/alert')

alert_model = alert_api.model('Alert', {
    'id': fields.Integer,
    'merchant_id': fields.Integer,
    'product_id': fields.Integer,
    'type': fields.String,
    'content': fields.String,
    'status': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
})

create_alert_model = alert_api.model('CreateAlert', {
    'product_id': fields.Integer(required=True, description='商品ID'),
    'type': fields.String(required=True, description='告警类型'),
    'content': fields.String(required=True, description='告警内容')
})

response_model = alert_api.model('Response', {
    'code': fields.Integer,
    'message': fields.String,
    'data': fields.Raw
})

@alert_api.route('/')
class AlertList(Resource):
    @login_required
    @alert_api.response(200, 'Success', response_model)
    def get(self):
        """获取告警列表"""
        alerts = Alert.query.filter_by(merchant_id=g.user.merchant_id).order_by(Alert.created_at.desc()).all()
        return {'code': 0, 'message': 'success', 'data': [alert.to_dict() for alert in alerts]}

    @login_required
    @alert_api.expect(create_alert_model)
    @alert_api.response(201, 'Created', response_model)
    def post(self):
        """创建告警"""
        data = request.json
        alert = Alert(
            merchant_id=g.user.merchant_id,
            product_id=data['product_id'],
            type=data['type'],
            content=data['content']
        )
        db.session.add(alert)
        db.session.commit()
        return {'code': 0, 'message': 'success', 'data': alert.to_dict()}, 201

@alert_api.route('/<int:alert_id>/handle')
class AlertHandle(Resource):
    @login_required
    @alert_api.response(200, 'Success', response_model)
    @alert_api.response(404, 'Not Found', response_model)
    def post(self, alert_id):
        """处理告警"""
        alert = Alert.query.filter_by(id=alert_id, merchant_id=g.user.merchant_id).first()
        if not alert:
            return {'code': 1, 'message': '告警不存在', 'data': None}, 404
        alert.status = 'handled'
        db.session.commit()
        return {'code': 0, 'message': 'success', 'data': alert.to_dict()} 