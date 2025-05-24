from app.extensions import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    merchant_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20))
    status = db.Column(db.Integer, default=1)
    stock = db.Column(db.Integer, default=0)
    warning_stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('merchant_id', 'sku', name='uix_merchant_sku'),
        db.Index('idx_merchant_name', 'merchant_id', 'name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'name': self.name,
            'sku': self.sku,
            'price': float(self.price),
            'unit': self.unit,
            'status': self.status,
            'stock': self.stock,
            'warning_stock': self.warning_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 