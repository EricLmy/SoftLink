from flask import Blueprint, request, jsonify
from flask_restx import Api, Resource, fields
from app.extensions import db
from app.models import Inventory, Product
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

bp = Blueprint('inventory', __name__)
inventory_api = Api(bp, doc='/inventory/doc', title='库存管理')

inventory_model = inventory_api.model('Inventory', {
    'id': fields.Integer(readonly=True),
    'product_id': fields.Integer(required=True),
    'merchant_id': fields.Integer,
    'quantity': fields.Integer,
    'warning_line': fields.Integer,
    'updated_at': fields.DateTime,
})

@inventory_api.route('/')
class InventoryList(Resource):
    @jwt_required()
    @inventory_api.marshal_list_with(inventory_model)
    def get(self):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        inventory = Inventory.query.filter_by(merchant_id=merchant_id).all()
        return inventory

@inventory_api.route('/<int:inventory_id>')
class InventoryDetail(Resource):
    @jwt_required()
    @inventory_api.marshal_with(inventory_model)
    def get(self, inventory_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        inv = Inventory.query.filter_by(id=inventory_id, merchant_id=merchant_id).first()
        if not inv:
            return {'msg': '库存不存在'}, 404
        return inv

    @jwt_required()
    @inventory_api.expect(inventory_model, validate=True)
    def put(self, inventory_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        inv = Inventory.query.filter_by(id=inventory_id, merchant_id=merchant_id).first()
        if not inv:
            return {'msg': '库存不存在'}, 404
        data = request.json
        inv.quantity = data['quantity']
        inv.warning_line = data.get('warning_line', inv.warning_line)
        inv.updated_at = datetime.utcnow()
        db.session.commit()
        return {'msg': '更新成功'}

@inventory_api.route('/<int:inventory_id>/check')
class InventoryCheck(Resource):
    @jwt_required()
    def post(self, inventory_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        inv = Inventory.query.filter_by(id=inventory_id, merchant_id=merchant_id).first()
        if not inv:
            return {'msg': '库存不存在'}, 404
        data = request.json
        inv.quantity = data['quantity']
        inv.updated_at = datetime.utcnow()
        db.session.commit()
        return {'msg': '盘点成功'}

@inventory_api.route('/<int:inventory_id>/warning')
class InventoryWarning(Resource):
    @jwt_required()
    def post(self, inventory_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        inv = Inventory.query.filter_by(id=inventory_id, merchant_id=merchant_id).first()
        if not inv:
            return {'msg': '库存不存在'}, 404
        data = request.json
        inv.warning_line = data['warning_line']
        db.session.commit()
        return {'msg': '告警设置成功'}

@bp.route('/inventory', methods=['GET'])
def get_inventory_list():
    """获取库存列表"""
    try:
        # 联表查询获取商品信息
        inventory_list = db.session.query(
            Inventory, 
            Product.name.label('product_name'),
            Product.sku.label('product_sku')
        ).join(
            Product, 
            Inventory.product_id == Product.id
        ).all()

        data = [{
            'id': inv.Inventory.id,
            'product_id': inv.Inventory.product_id,
            'product_name': inv.product_name,
            'product_sku': inv.product_sku,
            'quantity': inv.Inventory.quantity,
            'warning_line': inv.Inventory.warning_line,
            'updated_at': inv.Inventory.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for inv in inventory_list]

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@bp.route('/inventory/<int:inventory_id>/stocktaking', methods=['POST'])
def stocktaking(inventory_id):
    """库存盘点"""
    try:
        data = request.get_json()
        quantity = data.get('quantity')
        
        if quantity is None:
            return jsonify({
                'code': 400,
                'message': '库存数量不能为空'
            }), 400

        inventory = Inventory.query.get(inventory_id)
        if not inventory:
            return jsonify({
                'code': 404,
                'message': '库存记录不存在'
            }), 404

        inventory.quantity = quantity
        inventory.updated_at = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@bp.route('/inventory/<int:inventory_id>/warning-line', methods=['POST'])
def set_warning_line(inventory_id):
    """设置库存告警线"""
    try:
        data = request.get_json()
        warning_line = data.get('warning_line')
        
        if warning_line is None:
            return jsonify({
                'code': 400,
                'message': '告警线不能为空'
            }), 400

        inventory = Inventory.query.get(inventory_id)
        if not inventory:
            return jsonify({
                'code': 404,
                'message': '库存记录不存在'
            }), 404

        inventory.warning_line = warning_line
        inventory.updated_at = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500 