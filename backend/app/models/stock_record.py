from app.extensions import db
from datetime import datetime

class StockRecord(db.Model):
    """出入库记录"""
    __tablename__ = 'stock_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    merchant_id = db.Column(db.Integer, nullable=False, comment='商家ID')
    product_id = db.Column(db.Integer, nullable=False, comment='商品ID')
    type = db.Column(db.String(10), nullable=False, comment='类型：in-入库，out-出库')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    batch_number = db.Column(db.String(50), nullable=True, comment='批次号')
    operator = db.Column(db.String(50), nullable=False, comment='操作人')
    remark = db.Column(db.String(200), nullable=True, comment='备注')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f'<StockRecord {self.id}>' 