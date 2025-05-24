from flask import Blueprint, request, jsonify
from flask_restx import Api, Resource, fields
from app.extensions import db
from app.models import Order, OrderItem, Product, Inventory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

bp = Blueprint('order', __name__)
order_api = Api(bp, doc='/order/doc', title='订单管理')

order_item_model = order_api.model('OrderItem', {
    'product_id': fields.Integer(required=True),
    'quantity': fields.Integer(required=True),
    'price': fields.Float(required=True),
})

order_model = order_api.model('Order', {
    'customer_name': fields.String(required=True),
    'customer_phone': fields.String(),
    'items': fields.List(fields.Nested(order_item_model), required=True),
    'remark': fields.String(),
})

@bp.route('/order', methods=['GET'])
def get_order_list():
    """获取订单列表"""
    try:
        # 联表查询获取订单及其明细
        orders = Order.query.order_by(Order.created_at.desc()).all()
        
        data = []
        for order in orders:
            # 查询订单明细
            items = OrderItem.query.filter_by(order_id=order.id).all()
            items_data = []
            for item in items:
                # 获取商品信息
                product = Product.query.get(item.product_id)
                items_data.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name if product else None,
                    'product_sku': product.sku if product else None,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'amount': float(item.amount)
                })
            
            data.append({
                'id': order.id,
                'order_no': order.order_no,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'total_amount': float(order.total_amount),
                'status': order.status,
                'remark': order.remark,
                'operator': order.operator,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items_data
            })

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

@bp.route('/order', methods=['POST'])
def create_order():
    """创建订单"""
    try:
        data = request.get_json()
        customer_name = data.get('customer_name')
        items = data.get('items')
        
        if not customer_name or not items:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400

        # 生成订单编号
        order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8]}"
        
        # 计算订单总金额
        total_amount = sum(item['price'] * item['quantity'] for item in items)
        
        # 创建订单
        order = Order(
            order_no=order_no,
            merchant_id=1,  # TODO: 从JWT中获取merchant_id
            customer_name=customer_name,
            customer_phone=data.get('customer_phone'),
            total_amount=total_amount,
            status='pending',
            remark=data.get('remark'),
            operator='admin'  # TODO: 从JWT中获取operator
        )
        db.session.add(order)
        db.session.flush()  # 获取order.id
        
        # 创建订单明细并检查库存
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            price = item['price']
            
            # 检查商品是否存在
            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return jsonify({
                    'code': 404,
                    'message': f'商品ID {product_id} 不存在'
                }), 404
            
            # 检查库存是否充足
            inventory = Inventory.query.filter_by(product_id=product_id).first()
            if not inventory or inventory.quantity < quantity:
                db.session.rollback()
                return jsonify({
                    'code': 400,
                    'message': f'商品 {product.name} 库存不足'
                }), 400
            
            # 创建订单明细
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                price=price,
                amount=price * quantity
            )
            db.session.add(order_item)
            
            # 扣减库存
            inventory.quantity -= quantity

        db.session.commit()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'order_id': order.id,
                'order_no': order.order_no
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@bp.route('/order/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    """获取订单详情"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'code': 404,
                'message': '订单不存在'
            }), 404

        # 查询订单明细
        items = OrderItem.query.filter_by(order_id=order_id).all()
        items_data = []
        for item in items:
            # 获取商品信息
            product = Product.query.get(item.product_id)
            items_data.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': product.name if product else None,
                'product_sku': product.sku if product else None,
                'quantity': item.quantity,
                'price': float(item.price),
                'amount': float(item.amount)
            })

        data = {
            'id': order.id,
            'order_no': order.order_no,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'total_amount': float(order.total_amount),
            'status': order.status,
            'remark': order.remark,
            'operator': order.operator,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': items_data
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

@bp.route('/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """更新订单状态"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status or status not in ['pending', 'processing', 'completed', 'cancelled']:
            return jsonify({
                'code': 400,
                'message': '状态参数错误'
            }), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'code': 404,
                'message': '订单不存在'
            }), 404

        # 如果订单已完成或已取消，不允许修改状态
        if order.status in ['completed', 'cancelled']:
            return jsonify({
                'code': 400,
                'message': '订单已完成或已取消，无法修改状态'
            }), 400

        order.status = status
        order.updated_at = datetime.now()
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