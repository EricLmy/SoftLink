from app.extensions import db
from datetime import datetime

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, nullable=False)
    merchant_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    warning_line = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('product_id', 'merchant_id', name='uix_product_merchant'),
    ) 