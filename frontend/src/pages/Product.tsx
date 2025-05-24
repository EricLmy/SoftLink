import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Space, message, Popconfirm } from 'antd';
import axios from 'axios';

const Product: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/product/');
      setData(res.data);
    } catch (e) {
      message.error('获取商品列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAdd = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleDelete = async (record: any) => {
    try {
      await axios.delete(`/api/product/${record.id}`);
      message.success('删除成功');
      fetchData();
    } catch {
      message.error('删除失败');
    }
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (editing) {
        await axios.put(`/api/product/${editing.id}`, values);
        message.success('更新成功');
      } else {
        await axios.post('/api/product/', values);
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchData();
    } catch (e) {
      // 校验失败或请求失败
    }
  };

  const columns = [
    { title: '商品名称', dataIndex: 'name', key: 'name' },
    { title: 'SKU', dataIndex: 'sku', key: 'sku' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: number) => (v === 1 ? '启用' : '禁用') },
    { title: '操作', key: 'action', render: (_: any, record: any) => (
      <Space>
        <Button type="link" onClick={() => handleEdit(record)}>编辑</Button>
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record)}>
          <Button type="link" danger>删除</Button>
        </Popconfirm>
      </Space>
    ) },
  ];

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 12 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleAdd}>新增商品</Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} bordered />
      <Modal
        title={editing ? '编辑商品' : '新增商品'}
        open={modalOpen}
        onOk={handleOk}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="商品名称" rules={[{ required: true, message: '请输入商品名称' }]}> <Input /> </Form.Item>
          <Form.Item name="sku" label="SKU" rules={[{ required: true, message: '请输入SKU' }]}> <Input /> </Form.Item>
          <Form.Item name="unit" label="单位"> <Input /> </Form.Item>
          <Form.Item name="status" label="状态" initialValue={1} rules={[{ required: true }]}> <Input /> </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Product; 