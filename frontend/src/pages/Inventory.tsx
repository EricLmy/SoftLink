import React, { useState, useEffect } from 'react';
import { Table, Card, Button, Space, InputNumber, Modal, message, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import axios from 'axios';

interface InventoryItem {
  id: number;
  product_id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  warning_line: number;
  updated_at: string;
}

const Inventory: React.FC = () => {
  const [data, setData] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [stocktakingVisible, setStocktakingVisible] = useState(false);
  const [warningVisible, setWarningVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [newQuantity, setNewQuantity] = useState<number>(0);
  const [newWarningLine, setNewWarningLine] = useState<number>(0);

  // 获取库存列表
  const fetchInventory = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/inventory');
      setData(response.data.data);
    } catch (error) {
      message.error('获取库存数据失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  // 执行盘点
  const handleStocktaking = async () => {
    if (!selectedItem) return;
    try {
      await axios.post(`/api/inventory/${selectedItem.id}/stocktaking`, {
        quantity: newQuantity
      });
      message.success('盘点成功');
      setStocktakingVisible(false);
      fetchInventory();
    } catch (error) {
      message.error('盘点失败');
    }
  };

  // 设置告警线
  const handleWarningLine = async () => {
    if (!selectedItem) return;
    try {
      await axios.post(`/api/inventory/${selectedItem.id}/warning-line`, {
        warning_line: newWarningLine
      });
      message.success('设置告警线成功');
      setWarningVisible(false);
      fetchInventory();
    } catch (error) {
      message.error('设置告警线失败');
    }
  };

  const columns: ColumnsType<InventoryItem> = [
    {
      title: '商品SKU',
      dataIndex: 'product_sku',
      key: 'product_sku',
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: '当前库存',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number, record: InventoryItem) => (
        <span>
          {quantity}
          {record.warning_line && quantity <= record.warning_line && (
            <Tag color="red" style={{ marginLeft: 8 }}>库存不足</Tag>
          )}
        </span>
      ),
    },
    {
      title: '告警线',
      dataIndex: 'warning_line',
      key: 'warning_line',
    },
    {
      title: '最后更新',
      dataIndex: 'updated_at',
      key: 'updated_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button type="link" onClick={() => {
            setSelectedItem(record);
            setNewQuantity(record.quantity);
            setStocktakingVisible(true);
          }}>盘点</Button>
          <Button type="link" onClick={() => {
            setSelectedItem(record);
            setNewWarningLine(record.warning_line || 0);
            setWarningVisible(true);
          }}>设置告警</Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h2>库存管理</h2>
      <Card title="库存管理">
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
        />
      </Card>

      {/* 盘点弹窗 */}
      <Modal
        title="库存盘点"
        open={stocktakingVisible}
        onOk={handleStocktaking}
        onCancel={() => setStocktakingVisible(false)}
      >
        <div>
          <p>商品：{selectedItem?.product_name}</p>
          <p>当前库存：{selectedItem?.quantity}</p>
          <p>实际库存：
            <InputNumber
              value={newQuantity}
              onChange={(value) => setNewQuantity(value || 0)}
              min={0}
            />
          </p>
        </div>
      </Modal>

      {/* 告警设置弹窗 */}
      <Modal
        title="设置告警线"
        open={warningVisible}
        onOk={handleWarningLine}
        onCancel={() => setWarningVisible(false)}
      >
        <div>
          <p>商品：{selectedItem?.product_name}</p>
          <p>当前告警线：{selectedItem?.warning_line || '未设置'}</p>
          <p>新告警线：
            <InputNumber
              value={newWarningLine}
              onChange={(value) => setNewWarningLine(value || 0)}
              min={0}
            />
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default Inventory; 