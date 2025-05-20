import React, { useState, useEffect, useCallback } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, message, Typography, Space, Popconfirm, Spin, Tag, Tooltip, InputNumber, Card, Row, Col, TreeSelect, Switch
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, MenuOutlined, OrderedListOutlined, LinkOutlined, SafetyOutlined, AppstoreOutlined, FilterOutlined, ReloadOutlined
} from '@ant-design/icons';
// Assuming a service, e.g., menuService or featureService, for menu item admin operations
import { featureService } from '../services/api'; 

const { Title } = Typography;
const { Option } = Select;

// Helper to transform flat list to tree data for TreeSelect (parent_id selection)
const buildTreeData = (items, parentId = null) => {
  return items
    .filter(item => item.parent_id === parentId)
    .map(item => ({
      title: item.name,
      value: item.id,
      key: item.id,
      children: buildTreeData(items, item.id),
    }));
};

const AdminMenuPage = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [flatMenuItems, setFlatMenuItems] = useState([]); // For Parent ID selection
  const [pagination, setPagination] = useState({ current: 1, pageSize: 15, total: 0 }); // Show more items by default
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [sorter, setSorter] = useState({ field: 'order', order: 'ascend' }); // Default sort by order

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingMenuItem, setEditingMenuItem] = useState(null);
  
  const [featuresForSelect, setFeaturesForSelect] = useState([]);
  const [permissionsForSelect, setPermissionsForSelect] = useState([]); // Placeholder

  const [form] = Form.useForm();
  const [filterForm] = Form.useForm();

  const fetchMenuItems = useCallback(async (params = {}) => {
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
      const response = await featureService.adminGetMenuItems(queryParams); // GET /admin/dynamic-menu-items
      setMenuItems(response.data || []); // Assuming API returns flat list for table
      setFlatMenuItems(response.data || []); // Save flat list for parent selection tree
      // For a flat list without server pagination, total would be response.data.length
      // If server paginates (which it should for admin tables), use total from response
      setPagination(prev => ({ 
          ...prev, 
          total: response.data.total_items || response.data.length || 0 
        })); 
    } catch (error) {
      message.error('获取动态菜单列表失败。');
      console.error("Failed to fetch menu items:", error);
    }
    setLoading(false);
  }, [pagination.current, pagination.pageSize, filters, sorter]);

  const fetchAuxiliaryData = useCallback(async () => {
    try {
      // Fetch features for select dropdown
      const featuresResponse = await featureService.adminGetFeatures({per_page: 500}); // Get all features
      setFeaturesForSelect(featuresResponse.data.features || featuresResponse.data || []);
      
      // TODO: Fetch permissions for select dropdown from an API endpoint if available
      // For now, using placeholder. In a real app, this should be dynamic.
      setPermissionsForSelect([
        { name: 'view_dashboard', description: 'View Dashboard' }, 
        { name: 'manage_users', description: 'Manage Users' }
      ]);
    } catch (error) {
      message.error('获取关联数据（功能/权限）失败。');
    }
  }, []);

  useEffect(() => {
    fetchMenuItems();
    fetchAuxiliaryData();
  }, [fetchMenuItems, fetchAuxiliaryData]);

  const handleTableChange = (newPagination, newFilters, newSorter) => {
    setSorter(newSorter.field ? { field: newSorter.field, order: newSorter.order } : {});
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const onFilterSubmit = (values) => {
    const newFilters = Object.fromEntries(Object.entries(values).filter(([_, v]) => v !== undefined && v !== ''));
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const showEditModal = (menuItem = null) => {
    setEditingMenuItem(menuItem);
    form.resetFields();
    if (menuItem) {
      form.setFieldsValue({
        ...menuItem,
        // parent_id might need to be just the ID for TreeSelect
        parent_id: menuItem.parent_id,
        feature_identifier: menuItem.feature?.identifier || menuItem.feature_identifier,
      });
    }
    setIsModalVisible(true);
  };

  const handleModalSubmit = async (values) => {
    setLoading(true);
    try {
      const dataToSubmit = { ...values };
      if (dataToSubmit.parent_id === undefined) dataToSubmit.parent_id = null;
      if (dataToSubmit.feature_identifier === '') dataToSubmit.feature_identifier = null;
      if (dataToSubmit.required_permission_name === '') dataToSubmit.required_permission_name = null;

      if (editingMenuItem) {
        await featureService.adminUpdateMenuItem(editingMenuItem.id, dataToSubmit);
        message.success('菜单项更新成功！');
      } else {
        await featureService.adminCreateMenuItem(dataToSubmit);
        message.success('菜单项创建成功！');
      }
      setIsModalVisible(false);
      fetchMenuItems({ page: editingMenuItem ? pagination.current : 1 });
      fetchAuxiliaryData(); // Re-fetch in case names changed, though unlikely for features/permissions here
    } catch (error) {
      message.error(error.response?.data?.message || (editingMenuItem ? '更新失败' : '创建失败'));
    }
    setLoading(false);
  };

  const handleDeleteMenuItem = async (menuItemId, name) => {
    setLoading(true);
    try {
      await featureService.adminDeleteMenuItem(menuItemId);
      message.success(`菜单项 '${name}' 已删除。`);
      fetchMenuItems({ page: 1 });
    } catch (error) {
      message.error(error.response?.data?.message || '删除菜单项失败。可能存在子菜单项，请先处理子菜单项。');
    }
    setLoading(false);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: true },
    { title: '名称', dataIndex: 'name', key: 'name', sorter: true },
    { title: '图标', dataIndex: 'icon', key: 'icon', render: icon => icon || '-' },
    { title: 'URL/路径', dataIndex: 'url', key: 'url', render: url => url || '-' },
    { title: '父菜单ID', dataIndex: 'parent_id', key: 'parent_id', render: pid => pid || '无' , sorter: true },
    { title: '顺序', dataIndex: 'order', key: 'order', sorter: true, defaultSortOrder: 'ascend' },
    { title: '关联功能', dataIndex: ['feature', 'name'], key: 'feature_name', render: (name, record) => name || record.feature_identifier || '无' },
    { title: '所需权限', dataIndex: 'required_permission_name', key: 'required_permission_name', render: perm => perm || '无' },
    { title: '启用', dataIndex: 'is_enabled', key: 'is_enabled', render: enabled => <Tag color={enabled ? 'success' : 'error'}>{enabled ? '是' : '否'}</Tag>, sorter: true },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑菜单项">
            <Button size="small" icon={<EditOutlined />} onClick={() => showEditModal(record)} />
          </Tooltip>
          <Popconfirm
            title={`确定要删除菜单项 '${record.name}' 吗？如果它有子菜单，删除可能会失败。`}
            onConfirm={() => handleDeleteMenuItem(record.id, record.name)}
            okText="删除"
            cancelText="取消"
          >
            <Tooltip title="删除菜单项">
              <Button size="small" icon={<DeleteOutlined />} danger />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  
  const menuTreeData = buildTreeData(flatMenuItems);

  return (
    <Card>
      <Title level={3} style={{ marginBottom: '20px' }}>动态菜单项配置</Title>
      <Button 
        type="primary" 
        icon={<PlusOutlined />} 
        onClick={() => showEditModal(null)} 
        style={{ marginBottom: 16 }}
      >
        创建新菜单项
      </Button>
      {/* Filters can be added here if needed */}
      <Table 
        columns={columns} 
        dataSource={menuItems}
        rowKey="id" 
        pagination={pagination}
        loading={loading} 
        onChange={handleTableChange}
        scroll={{ x: 'max-content' }}
      />

      <Modal
        title={editingMenuItem ? '编辑菜单项' : '创建新菜单项'}
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={loading}
        destroyOnClose
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleModalSubmit} initialValues={{order: 0, is_enabled: true}}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="菜单名称" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="parent_id" label="父级菜单">
                <TreeSelect
                  treeData={menuTreeData}
                  placeholder="不选则为顶级菜单"
                  allowClear
                  treeDefaultExpandAll
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="url" label="URL/路径" rules={[{ required: true }]}>
                <Input prefix={<LinkOutlined />} placeholder="例如: /dashboard, /settings/profile" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="icon" label="图标名称 (可选)">
                <Input prefix={<MenuOutlined />} placeholder="Ant Design Icon name, e.g., home" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="feature_identifier" label="关联功能模块 (可选)">
                <Select placeholder="选择关联的功能" allowClear>
                  {featuresForSelect.map(f => <Option key={f.identifier} value={f.identifier}>{f.name} ({f.identifier})</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="required_permission_name" label="访问所需权限 (可选)">
                <Select placeholder="选择所需权限" allowClear>
                   {permissionsForSelect.map(p => <Option key={p.name} value={p.name}>{p.description} ({p.name})</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="order" label="显示顺序" rules={[{ type: 'number' }]}>
                <InputNumber style={{width: '100%'}} prefix={<OrderedListOutlined />} placeholder="数字越小越靠前" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_enabled" label="是否启用" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>
          {editingMenuItem && <Form.Item name="id" hidden><Input /></Form.Item>}
        </Form>
      </Modal>
    </Card>
  );
};

export default AdminMenuPage; 