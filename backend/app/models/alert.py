from datetime import datetime
from app.extensions import db

class Alert(db.Model):
    """告警记录模型"""
    __tablename__ = 'alert'

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # inventory_low: 库存不足, stock_warning: 库存预警
    content = db.Column(db.String(200), nullable=False)  # 告警内容
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending: 待处理, handled: 已处理
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    merchant = db.relationship('Merchant', backref=db.backref('alerts', lazy=True))
    product = db.relationship('Product', backref=db.backref('alerts', lazy=True))

    def __repr__(self):
        return f'<Alert {self.id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'type': self.type,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } 