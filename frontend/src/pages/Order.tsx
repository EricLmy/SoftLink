import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, Select, message, Space, Card } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  price: number;
  amount: number;
}

interface Order {
  id: number;
  order_no: string;
  customer_name: string;
  customer_phone: string;
  total_amount: number;
  status: string;
  remark: string;
  operator: string;
  created_at: string;
  items: OrderItem[];
}

interface Product {
  id: number;
  name: string;
  sku: string;
  price: number;
}

const Order: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [form] = Form.useForm();

  // 获取订单列表
  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/order`);
      if (response.data.code === 0) {
        setOrders(response.data.data);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('获取订单列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取商品列表
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
    fetchOrders();
    fetchProducts();
  }, []);

  // 创建订单
  const handleCreate = async (values: any) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/order`, values);
      if (response.data.code === 0) {
        message.success('创建订单成功');
        setCreateModalVisible(false);
        form.resetFields();
        fetchOrders();
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('创建订单失败');
    }
  };

  // 更新订单状态
  const handleUpdateStatus = async (orderId: number, status: string) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/order/${orderId}/status`, { status });
      if (response.data.code === 0) {
        message.success('更新订单状态成功');
        fetchOrders();
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('更新订单状态失败');
    }
  };

  // 查看订单详情
  const handleViewDetail = (record: Order) => {
    setSelectedOrder(record);
    setDetailModalVisible(true);
  };

  const columns = [
    {
      title: '订单编号',
      dataIndex: 'order_no',
      key: 'order_no',
    },
    {
      title: '客户姓名',
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: '客户电话',
      dataIndex: 'customer_phone',
      key: 'customer_phone',
    },
    {
      title: '订单金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount: number) => `¥${amount.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          pending: '待处理',
          processing: '处理中',
          completed: '已完成',
          cancelled: '已取消',
        };
        return statusMap[status as keyof typeof statusMap] || status;
      },
    },
    {
      title: '操作员',
      dataIndex: 'operator',
      key: 'operator',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Order) => (
        <Space>
          <Button type="link" onClick={() => handleViewDetail(record)}>
            查看详情
          </Button>
          {record.status === 'pending' && (
            <Button type="link" onClick={() => handleUpdateStatus(record.id, 'processing')}>
              开始处理
            </Button>
          )}
          {record.status === 'processing' && (
            <Button type="link" onClick={() => handleUpdateStatus(record.id, 'completed')}>
              完成订单
            </Button>
          )}
          {record.status !== 'completed' && record.status !== 'cancelled' && (
            <Button type="link" danger onClick={() => handleUpdateStatus(record.id, 'cancelled')}>
              取消订单
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            新建订单
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={orders}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />

        {/* 创建订单弹窗 */}
        <Modal
          title="新建订单"
          visible={createModalVisible}
          onCancel={() => setCreateModalVisible(false)}
          footer={null}
          width={800}
        >
          <Form form={form} onFinish={handleCreate} layout="vertical">
            <Form.Item
              name="customer_name"
              label="客户姓名"
              rules={[{ required: true, message: '请输入客户姓名' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item name="customer_phone" label="客户电话">
              <Input />
            </Form.Item>

            <Form.List name="items">
              {(fields, { add, remove }) => (
                <>
                  {fields.map((field, index) => (
                    <Card key={field.key} style={{ marginBottom: 16 }} size="small">
                      <Space align="baseline">
                        <Form.Item
                          {...field}
                          name={[field.name, 'product_id']}
                          label="商品"
                          rules={[{ required: true, message: '请选择商品' }]}
                        >
                          <Select style={{ width: 200 }}>
                            {products.map((product) => (
                              <Select.Option key={product.id} value={product.id}>
                                {product.name} ({product.sku})
                              </Select.Option>
                            ))}
                          </Select>
                        </Form.Item>

                        <Form.Item
                          {...field}
                          name={[field.name, 'quantity']}
                          label="数量"
                          rules={[{ required: true, message: '请输入数量' }]}
                        >
                          <InputNumber min={1} />
                        </Form.Item>

                        <Form.Item
                          {...field}
                          name={[field.name, 'price']}
                          label="单价"
                          rules={[{ required: true, message: '请输入单价' }]}
                        >
                          <InputNumber min={0} precision={2} />
                        </Form.Item>

                        <Button type="link" danger onClick={() => remove(field.name)}>
                          删除
                        </Button>
                      </Space>
                    </Card>
                  ))}

                  <Form.Item>
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      添加商品
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>

            <Form.Item name="remark" label="备注">
              <Input.TextArea />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
            </Form.Item>
          </Form>
        </Modal>

        {/* 订单详情弹窗 */}
        <Modal
          title="订单详情"
          visible={detailModalVisible}
          onCancel={() => setDetailModalVisible(false)}
          footer={null}
          width={800}
        >
          {selectedOrder && (
            <div>
              <p>订单编号：{selectedOrder.order_no}</p>
              <p>客户姓名：{selectedOrder.customer_name}</p>
              <p>客户电话：{selectedOrder.customer_phone}</p>
              <p>订单状态：{selectedOrder.status}</p>
              <p>订单金额：¥{selectedOrder.total_amount.toFixed(2)}</p>
              <p>备注：{selectedOrder.remark}</p>
              <p>操作员：{selectedOrder.operator}</p>
              <p>创建时间：{selectedOrder.created_at}</p>

              <Table
                columns={[
                  { title: '商品SKU', dataIndex: 'product_sku', key: 'product_sku' },
                  { title: '商品名称', dataIndex: 'product_name', key: 'product_name' },
                  { title: '数量', dataIndex: 'quantity', key: 'quantity' },
                  {
                    title: '单价',
                    dataIndex: 'price',
                    key: 'price',
                    render: (price: number) => `¥${price.toFixed(2)}`,
                  },
                  {
                    title: '金额',
                    dataIndex: 'amount',
                    key: 'amount',
                    render: (amount: number) => `¥${amount.toFixed(2)}`,
                  },
                ]}
                dataSource={selectedOrder.items}
                pagination={false}
                rowKey="id"
              />
            </div>
          )}
        </Modal>
      </Card>
    </div>
  );
};

export default Order; 