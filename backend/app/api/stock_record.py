from flask import Blueprint, request, jsonify
from flask_restx import Api, Resource, fields
from app.extensions import db
from app.models import StockRecord, Product, Inventory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

bp = Blueprint('stock_record', __name__)
stock_record_api = Api(bp, doc='/stock-record/doc', title='出入库管理')

stock_record_model = stock_record_api.model('StockRecord', {
    'id': fields.Integer(readonly=True),
    'product_id': fields.Integer(required=True),
    'type': fields.String(required=True, enum=['in', 'out']),
    'quantity': fields.Integer(required=True),
    'batch_number': fields.String(),
    'operator': fields.String(required=True),
    'remark': fields.String(),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True),
})

@bp.route('/stock-record', methods=['GET'])
def get_stock_record_list():
    """获取出入库记录列表"""
    try:
        # 联表查询获取商品信息
        stock_record_list = db.session.query(
            StockRecord, 
            Product.name.label('product_name'),
            Product.sku.label('product_sku')
        ).join(
            Product, 
            StockRecord.product_id == Product.id
        ).all()

        data = [{
            'id': record.StockRecord.id,
            'product_id': record.StockRecord.product_id,
            'product_name': record.product_name,
            'product_sku': record.product_sku,
            'type': record.StockRecord.type,
            'quantity': record.StockRecord.quantity,
            'batch_number': record.StockRecord.batch_number,
            'operator': record.StockRecord.operator,
            'remark': record.StockRecord.remark,
            'created_at': record.StockRecord.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for record in stock_record_list]

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

@bp.route('/stock-record', methods=['POST'])
def create_stock_record():
    """创建出入库记录"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        record_type = data.get('type')
        quantity = data.get('quantity')
        operator = data.get('operator')
        
        if not all([product_id, record_type, quantity, operator]):
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400

        if record_type not in ['in', 'out']:
            return jsonify({
                'code': 400,
                'message': '出入库类型错误'
            }), 400

        # 检查商品是否存在
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'code': 404,
                'message': '商品不存在'
            }), 404

        # 创建出入库记录
        stock_record = StockRecord(
            product_id=product_id,
            merchant_id=product.merchant_id,
            type=record_type,
            quantity=quantity,
            batch_number=data.get('batch_number'),
            operator=operator,
            remark=data.get('remark')
        )
        db.session.add(stock_record)

        # 更新库存
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            inventory = Inventory(
                product_id=product_id,
                merchant_id=product.merchant_id,
                quantity=0,
                warning_line=0
            )
            db.session.add(inventory)

        if record_type == 'in':
            inventory.quantity += quantity
        else:  # out
            if inventory.quantity < quantity:
                return jsonify({
                    'code': 400,
                    'message': '库存不足'
                }), 400
            inventory.quantity -= quantity

        db.session.commit()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'id': stock_record.id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@bp.route('/stock-record/<int:record_id>', methods=['GET'])
def get_stock_record_detail(record_id):
    """获取出入库记录详情"""
    try:
        record = db.session.query(
            StockRecord, 
            Product.name.label('product_name'),
            Product.sku.label('product_sku')
        ).join(
            Product, 
            StockRecord.product_id == Product.id
        ).filter(
            StockRecord.id == record_id
        ).first()

        if not record:
            return jsonify({
                'code': 404,
                'message': '记录不存在'
            }), 404

        data = {
            'id': record.StockRecord.id,
            'product_id': record.StockRecord.product_id,
            'product_name': record.product_name,
            'product_sku': record.product_sku,
            'type': record.StockRecord.type,
            'quantity': record.StockRecord.quantity,
            'batch_number': record.StockRecord.batch_number,
            'operator': record.StockRecord.operator,
            'remark': record.StockRecord.remark,
            'created_at': record.StockRecord.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

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