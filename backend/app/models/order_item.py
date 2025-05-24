from app.extensions import db
from datetime import datetime

class OrderItem(db.Model):
    """订单明细"""
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, nullable=False, comment='订单ID')
    product_id = db.Column(db.Integer, nullable=False, comment='商品ID')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    price = db.Column(db.Numeric(10, 2), nullable=False, comment='单价')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='金额')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f'<OrderItem {self.id}>' 