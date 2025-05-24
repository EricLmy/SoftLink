from app.extensions import db
from datetime import datetime

class Order(db.Model):
    """订单"""
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    merchant_id = db.Column(db.Integer, nullable=False, comment='商家ID')
    order_no = db.Column(db.String(50), nullable=False, unique=True, comment='订单编号')
    customer_name = db.Column(db.String(100), nullable=False, comment='客户名称')
    customer_phone = db.Column(db.String(20), nullable=True, comment='客户电话')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='订单总金额')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='状态：pending-待处理，processing-处理中，completed-已完成，cancelled-已取消')
    remark = db.Column(db.String(200), nullable=True, comment='备注')
    operator = db.Column(db.String(50), nullable=False, comment='操作人')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f'<Order {self.order_no}>'

class OrderItem(db.Model):
    """订单项"""
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, comment='订单ID')
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, comment='商品ID')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    price = db.Column(db.Numeric(10, 2), nullable=False, comment='单价')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='金额')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    order = db.relationship('Order', backref=db.backref('items', lazy=True))
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))

    def __repr__(self):
        return f'<OrderItem {self.id}>' 