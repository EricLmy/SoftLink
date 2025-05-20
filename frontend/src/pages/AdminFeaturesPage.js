import React, { useState, useEffect, useCallback } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Switch, message, Typography, Space, Popconfirm, Spin, Tag, Tooltip, InputNumber, Card, Row, Col
} from 'antd';
import {
  PlusOutlined, EditOutlined, FilterOutlined, ReloadOutlined, AppstoreAddOutlined
} from '@ant-design/icons';
import moment from 'moment';
// Assuming featureService will house admin methods for features or a dedicated adminService is used
import { featureService, vipService } from '../services/api'; 

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const AdminFeaturesPage = () => {
  const [features, setFeatures] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [sorter, setSorter] = useState({});

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingFeature, setEditingFeature] = useState(null);
  const [vipLevels, setVipLevels] = useState([]);

  const [form] = Form.useForm();
  const [filterForm] = Form.useForm();

  const fetchFeatures = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        page: params.page || pagination.current,
        per_page: params.per_page || pagination.pageSize,
        ...filters,
      };
      if (sorter.field) {
        queryParams.sort_by = sorter.field;
        queryParams.order = sorter.order === 'ascend' ? 'asc' : 'desc';
      }
      // Ensure featureService.adminGetFeatures or similar exists and handles these params
      const response = await featureService.adminGetFeatures(queryParams); 
      setFeatures(response.data.features || response.data || []); // Adjust based on actual API response
      setPagination({
        current: response.data.current_page || 1,
        pageSize: queryParams.per_page,
        total: response.data.total_features || response.data.length || 0,
      });
    } catch (error) {
      message.error('获取功能模块列表失败。');
      console.error("Failed to fetch features:", error);
    }
    setLoading(false);
  }, [pagination.current, pagination.pageSize, filters, sorter]);

  const fetchVipLevelsForSelect = useCallback(async () => {
    try {
      const response = await vipService.getVipLevels(); // GET /vip/levels
      setVipLevels(response.data || []);
    } catch (error) {
      message.error('获取VIP等级列表失败，无法填充选择框。');
    }
  }, []);

  useEffect(() => {
    fetchFeatures();
    fetchVipLevelsForSelect();
  }, [fetchFeatures, fetchVipLevelsForSelect]);

  const handleTableChange = (newPagination, newFilters, newSorter) => {
    setSorter(newSorter.field ? { field: newSorter.field, order: newSorter.order } : {});
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const onFilterSubmit = (values) => {
    const newFilters = Object.fromEntries(Object.entries(values).filter(([_, v]) => v !== undefined && v !== ''));
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const showEditModal = (feature = null) => {
    setEditingFeature(feature);
    form.resetFields();
    if (feature) {
      form.setFieldsValue({ 
        ...feature,
        min_vip_level_required_id: feature.min_vip_level_required?.id || feature.min_vip_level_required_id 
      });
    }
    setIsModalVisible(true);
  };

  const handleModalSubmit = async (values) => {
    setLoading(true);
    try {
      const dataToSubmit = { ...values };
      if (dataToSubmit.min_vip_level_required_id === undefined) {
        dataToSubmit.min_vip_level_required_id = null; // Ensure it's null if not selected
      }

      if (editingFeature) {
        await featureService.adminUpdateFeature(editingFeature.id, dataToSubmit);
        message.success('功能模块更新成功！');
      } else {
        await featureService.adminCreateFeature(dataToSubmit);
        message.success('功能模块创建成功！');
      }
      setIsModalVisible(false);
      fetchFeatures({ page: editingFeature ? pagination.current : 1 });
    } catch (error) {
      message.error(error.response?.data?.message || (editingFeature ? '更新失败' : '创建失败'));
    }
    setLoading(false);
  };

  // No delete for features in MVP, only enable/disable via edit modal.

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: true },
    { title: '名称', dataIndex: 'name', key: 'name', sorter: true },
    { title: '标识符', dataIndex: 'identifier', key: 'identifier', sorter: true, render: id => <Tag color="geekblue">{id}</Tag> },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '核心功能', dataIndex: 'is_core_feature', key: 'is_core_feature', render: core => <Tag color={core ? 'green' : 'orange'}>{core ? '是' : '否'}</Tag>, sorter: true },
    { title: '试用天数', dataIndex: 'trial_days', key: 'trial_days', sorter: true },
    { title: '最低VIP等级', dataIndex: ['min_vip_level_required', 'name'], key: 'min_vip_level', render: name => name || '无要求' },
    { title: '启用状态', dataIndex: 'is_enabled', key: 'is_enabled', render: enabled => <Tag color={enabled ? 'success' : 'error'}>{enabled ? '已启用' : '已禁用'}</Tag>, sorter: true },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: text => moment(text).format('YYYY-MM-DD'), sorter: true },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 100,
      render: (_, record) => (
        <Tooltip title="编辑功能模块">
          <Button size="small" icon={<EditOutlined />} onClick={() => showEditModal(record)} />
        </Tooltip>
      ),
    },
  ];

  const FeatureFilterForm = (
    <Form form={filterForm} layout="inline" onFinish={onFilterSubmit} style={{ marginBottom: 16 }}>
        <Form.Item name="name"><Input placeholder="名称" allowClear /></Form.Item>
        <Form.Item name="identifier"><Input placeholder="标识符" allowClear /></Form.Item>
        <Form.Item name="is_enabled">
            <Select placeholder="启用状态" allowClear style={{width: 120}}>
                <Option value={true}>已启用</Option>
                <Option value={false}>已禁用</Option>
            </Select>
        </Form.Item>
        <Form.Item>
            <Button type="primary" htmlType="submit" icon={<FilterOutlined />}>筛选</Button>
        </Form.Item>
        <Form.Item>
            <Button onClick={() => { filterForm.resetFields(); setFilters({}); fetchFeatures({page: 1}); }} icon={<ReloadOutlined />}>重置</Button>
        </Form.Item>
    </Form>
  );

  return (
    <Card>
      <Title level={3} style={{ marginBottom: '20px' }}>功能模块配置</Title>
      <Button 
        type="primary" 
        icon={<PlusOutlined />} 
        onClick={() => showEditModal(null)} 
        style={{ marginBottom: 16 }}
      >
        创建新功能模块
      </Button>
      {FeatureFilterForm}
      <Table 
        columns={columns} 
        dataSource={features}
        rowKey="id" 
        pagination={pagination}
        loading={loading} 
        onChange={handleTableChange}
        scroll={{ x: 'max-content' }}
      />

      <Modal
        title={editingFeature ? '编辑功能模块' : '创建新功能模块'}
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()} // Trigger form submission from Ok button
        confirmLoading={loading} // Show loading on Ok button during submit
        destroyOnClose
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleModalSubmit}>
          <Form.Item name="name" label="功能名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="identifier" label="唯一标识符 (Identifier)" rules={[{ required: true, message: '请输入唯一标识符, 例如: online_inventory'}]}>
            <Input disabled={!!editingFeature} placeholder="例如: online_inventory, finance_report" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="base_url" label="基础URL/路径 (可选)">
                <Input placeholder="例如: /inventory, /reports/finance" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="icon" label="菜单图标 (可选)">
                <Input placeholder="例如: home, user, setting (Ant Design Icon name or custom)" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="is_core_feature" label="核心功能" valuePropName="checked">
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
            <Col span={8}>
                <Form.Item name="trial_days" label="试用天数 (非VIP)" initialValue={7} rules={[{ type: 'number', min: 0 }]}>
                    <InputNumber style={{width: '100%'}} />
                </Form.Item>
            </Col>
             <Col span={8}>
                <Form.Item name="is_enabled" label="启用状态" valuePropName="checked" initialValue={true}>
                    <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
            </Col>
          </Row>
          <Form.Item name="min_vip_level_required_id" label="最低VIP等级要求 (试用后)">
            <Select placeholder="选择VIP等级 (不选则无要求)" allowClear>
              {vipLevels.map(level => (
                <Option key={level.id} value={level.id}>{level.name}</Option>
              ))}
            </Select>
          </Form.Item>
          {/* Hidden ID field for editing */}
          {editingFeature && <Form.Item name="id" hidden><Input /></Form.Item>}
        </Form>
      </Modal>
    </Card>
  );
};

export default AdminFeaturesPage; 