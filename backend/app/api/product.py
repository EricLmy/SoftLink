from flask import Blueprint, request
from flask_restx import Api, Resource, fields
from app.extensions import db
from app.models import Product
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

bp = Blueprint('product', __name__)
product_api = Api(bp, doc='/product/doc', title='商品管理')

product_model = product_api.model('Product', {
    'id': fields.Integer(readonly=True),
    'merchant_id': fields.Integer,
    'name': fields.String(required=True, description='商品名称'),
    'sku': fields.String(required=True, description='SKU'),
    'unit': fields.String(description='单位'),
    'status': fields.Integer,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
})

@product_api.route('/')
class ProductList(Resource):
    @jwt_required()
    @product_api.marshal_list_with(product_model)
    def get(self):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        products = Product.query.filter_by(merchant_id=merchant_id).all()
        return products

    @jwt_required()
    @product_api.expect(product_model, validate=True)
    def post(self):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        data = request.json
        if Product.query.filter_by(merchant_id=merchant_id, sku=data['sku']).first():
            return {'msg': 'SKU已存在'}, 400
        product = Product(
            merchant_id=merchant_id,
            name=data['name'],
            sku=data['sku'],
            unit=data.get('unit'),
            status=data.get('status', 1)
        )
        db.session.add(product)
        db.session.commit()
        return {'msg': '创建成功', 'id': product.id}, 201

@product_api.route('/<int:product_id>')
class ProductDetail(Resource):
    @jwt_required()
    @product_api.marshal_with(product_model)
    def get(self, product_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
        if not product:
            return {'msg': '商品不存在'}, 404
        return product

    @jwt_required()
    @product_api.expect(product_model, validate=True)
    def put(self, product_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
        if not product:
            return {'msg': '商品不存在'}, 404
        data = request.json
        product.name = data['name']
        product.sku = data['sku']
        product.unit = data.get('unit')
        product.status = data.get('status', 1)
        product.updated_at = datetime.utcnow()
        db.session.commit()
        return {'msg': '更新成功'}

    @jwt_required()
    def delete(self, product_id):
        identity = get_jwt_identity()
        merchant_id = identity['merchant_id']
        product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
        if not product:
            return {'msg': '商品不存在'}, 404
        db.session.delete(product)
        db.session.commit()
        return {'msg': '删除成功'} 