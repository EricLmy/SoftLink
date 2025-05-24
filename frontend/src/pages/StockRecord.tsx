import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface StockRecordItem {
  id: number;
  product_id: number;
  product_name: string;
  product_sku: string;
  type: 'in' | 'out';
  quantity: number;
  batch_number?: string;
  operator: string;
  remark?: string;
  created_at: string;
}

const StockRecord: React.FC = () => {
  const [records, setRecords] = useState<StockRecordItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [products, setProducts] = useState<Array<{ id: number; name: string; sku: string }>>([]);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/stock-record`);
      if (response.data.code === 0) {
        setRecords(response.data.data);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('获取出入库记录失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/product`);
      if (response.data.code === 0) {
        setProducts(response.data.data);
      }
    } catch (error) {
      message.error('获取商品列表失败');
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchProducts();
  }, []);

  const handleCreate = async (values: any) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/stock-record`, values);
      if (response.data.code === 0) {
        message.success('创建成功');
        setModalVisible(false);
        form.resetFields();
        fetchRecords();
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('创建失败');
    }
  };

  const columns = [
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
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (type === 'in' ? '入库' : '出库'),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '批次号',
      dataIndex: 'batch_number',
      key: 'batch_number',
    },
    {
      title: '操作人',
      dataIndex: 'operator',
      key: 'operator',
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          新建出入库记录
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={records}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="新建出入库记录"
        visible={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          onFinish={handleCreate}
          layout="vertical"
        >
          <Form.Item
            name="product_id"
            label="商品"
            rules={[{ required: true, message: '请选择商品' }]}
          >
            <Select>
              {products.map(product => (
                <Select.Option key={product.id} value={product.id}>
                  {product.name} ({product.sku})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select>
              <Select.Option value="in">入库</Select.Option>
              <Select.Option value="out">出库</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="quantity"
            label="数量"
            rules={[{ required: true, message: '请输入数量' }]}
          >
            <Input type="number" min={1} />
          </Form.Item>

          <Form.Item
            name="batch_number"
            label="批次号"
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="operator"
            label="操作人"
            rules={[{ required: true, message: '请输入操作人' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="remark"
            label="备注"
          >
            <Input.TextArea />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                form.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default StockRecord; 