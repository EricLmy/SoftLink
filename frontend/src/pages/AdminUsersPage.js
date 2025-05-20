import React, { useState, useEffect, useCallback } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, DatePicker, message, Typography, Space, Popconfirm, Spin, Tag, Tooltip, InputNumber, Row, Col, Card
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, CrownOutlined, SearchOutlined, ReloadOutlined, FilterOutlined, QuestionCircleOutlined
} from '@ant-design/icons';
import { userService } from '../services/api'; // Using userService, assuming it has admin methods or we create adminService
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;

// Helper function to get role display name (if needed)
const getRoleDisplayName = (role) => {
  const roles = {
    super_admin: '超级管理员',
    parent_user: '父账户',
    sub_account: '子账户',
    developer: '开发者',
  };
  return roles[role] || role;
};

const AdminUsersPage = () => {
  const [users, setUsers] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({}); // For server-side filtering
  const [sorter, setSorter] = useState({}); // For server-side sorting

  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [isVipModalVisible, setIsVipModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  
  const [vipLevels, setVipLevels] = useState([]); // To store VIP levels for selection

  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [vipForm] = Form.useForm();
  const [filterForm] = Form.useForm(); // For filter inputs

  const fetchUsers = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        page: params.page || pagination.current,
        per_page: params.per_page || pagination.pageSize,
        ...filters, // Include current filters
        // Add sorting if API supports it: sort_by: sorter.field, order: sorter.order === 'ascend' ? 'asc' : 'desc'
      };
      if (sorter.field) {
        queryParams.sort_by = sorter.field;
        queryParams.order = sorter.order === 'ascend' ? 'asc' : 'desc';
      }

      const response = await userService.adminGetUsers(queryParams); // GET /admin/users
      setUsers(response.data.users || []);
      setPagination({
        current: response.data.current_page || 1,
        pageSize: queryParams.per_page,
        total: response.data.total_users || 0,
      });
    } catch (error) {
      message.error('获取用户列表失败，请稍后重试。');
      console.error("Failed to fetch users:", error);
    }
    setLoading(false);
  }, [pagination.current, pagination.pageSize, filters, sorter]);

  // Fetch VIP levels for VIP modal (assuming an endpoint exists)
  const fetchVipLevels = useCallback(async () => {
    try {
        // Replace with actual API call to get VIP levels, e.g., from featureService or a new vipService
        // const response = await vipService.getVipLevels(); 
        // setVipLevels(response.data);
        // For now, using placeholder data if API is not ready
        setVipLevels([
            { id: 1, name: 'VIP 1' }, { id: 2, name: 'VIP 2' }, { id: 3, name: 'VIP 3 (Lifetime)' }
        ]);
    } catch (error) {
        message.error('获取VIP等级列表失败。');
    }
  }, []);

  useEffect(() => {
    fetchUsers();
    fetchVipLevels();
  }, [fetchUsers, fetchVipLevels]); // fetchUsers will re-run if pagination, filters, or sorter change

  const handleTableChange = (newPagination, newFilters, newSorter) => {
    // API filters are handled by the filterForm, this newFilters from AntD table might be different
    // For server-side sorting:
    setSorter(newSorter.field ? { field: newSorter.field, order: newSorter.order } : {});
    // Pagination is handled by API response, but we can update our state to trigger fetch
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
    // fetchUsers will be called by useEffect due to sorter/pagination dependency change
  };
  
  const onFilterSubmit = (values) => {
    const newFilters = {};
    for (const key in values) {
        if (values[key]) { // Only add if value is present
            newFilters[key] = values[key];
        }
    }
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, current: 1 })); // Reset to first page on new filter
    // fetchUsers will be called by useEffect
  };

  // --- Create User Handlers ---
  const showCreateModal = () => {
    createForm.resetFields();
    setIsCreateModalVisible(true);
  };

  const handleCreateUser = async (values) => {
    setLoading(true);
    try {
      await userService.adminCreateUser(values); // POST /admin/users
      message.success('用户创建成功！');
      setIsCreateModalVisible(false);
      fetchUsers({ page: 1 }); // Refresh list and go to first page
    } catch (error) {
      message.error(error.response?.data?.message || '用户创建失败。');
    }
    setLoading(false);
  };

  // --- Edit User Handlers ---
  const showEditModal = (record) => {
    setEditingRecord(record);
    editForm.setFieldsValue({ 
        ...record, 
        // password field should be empty for updates, or handled differently
    });
    setIsEditModalVisible(true);
  };

  const handleEditUser = async (values) => {
    setLoading(true);
    try {
      const updateData = { ...values };
      delete updateData.username; // Username typically not editable by admin to avoid issues, or backend validates carefully
      delete updateData.password; // Password changes should be a separate flow for admin

      await userService.adminUpdateUser(editingRecord.id, updateData); // PUT /admin/users/{id}
      message.success(`用户 ${editingRecord.username} 信息更新成功。`);
      setIsEditModalVisible(false);
      fetchUsers();
    } catch (error) {
      message.error(error.response?.data?.message || '用户信息更新失败。');
    }
    setLoading(false);
  };

  // --- VIP Status Handlers ---
  const showVipModal = (record) => {
    setEditingRecord(record);
    vipForm.setFieldsValue({
        vip_level_id: record.vip_level_id,
        vip_expiry_date: record.vip_expiry_date ? moment(record.vip_expiry_date) : null,
    });
    setIsVipModalVisible(true);
  };

  const handleUpdateVipStatus = async (values) => {
    setLoading(true);
    try {
      const dataToSubmit = {
        vip_level_id: values.vip_level_id,
        vip_expiry_date_str: values.vip_expiry_date ? values.vip_expiry_date.format('YYYY-MM-DD HH:mm:ss') : null,
      };
      await userService.adminUpdateUserVipStatus(editingRecord.id, dataToSubmit); // PUT /admin/users/{id}/vip
      message.success(`用户 ${editingRecord.username} 的VIP状态已更新。`);
      setIsVipModalVisible(false);
      fetchUsers();
    } catch (error) {
      message.error(error.response?.data?.message || 'VIP状态更新失败。');
    }
    setLoading(false);
  };
  
  // --- Delete User Handler ---
  const handleDeleteUser = async (userId, username) => {
    setLoading(true);
    try {
      await userService.adminDeleteUser(userId); // DELETE /admin/users/{id}
      message.success(`用户 ${username} 已成功删除。`);
      fetchUsers({ page: 1 }); // Refresh list and go to first page if current page becomes empty
    } catch (error) {
      message.error(error.response?.data?.message || '删除用户失败。');
    }
    setLoading(false);
  };

  const userColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: true }, // Enable server-side sorting
    { title: '用户名', dataIndex: 'username', key: 'username', sorter: true },
    { title: '邮箱', dataIndex: 'email', key: 'email', sorter: true },
    {
      title: '角色', 
      dataIndex: 'role', 
      key: 'role', 
      render: role => <Tag color="blue">{getRoleDisplayName(role)}</Tag>,
      sorter: true
    },
    {
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: status => (
        <Tag color={status === 'active' ? 'green' : (status === 'suspended' ? 'orange' : 'volcano')}>
          {status ? status.toUpperCase() : 'N/A'}
        </Tag>
      ),
      sorter: true
    },
    { title: 'VIP 等级', dataIndex: 'vip_level_name', key: 'vip_level_name', render: name => name || '-' }, // Assuming vip_level_name from UserInfoSchema
    { title: 'VIP 到期', dataIndex: 'vip_expiry_date', key: 'vip_expiry_date', render: (text) => text ? moment(text).format('YYYY-MM-DD') : '-', sorter: true },
    { title: '上次登录', dataIndex: 'last_login_at', key: 'last_login_at', render: (text) => text ? moment(text).format('YYYY-MM-DD HH:mm') : 'N/A', sorter: true },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑用户">
            <Button size="small" icon={<EditOutlined />} onClick={() => showEditModal(record)} />
          </Tooltip>
          <Tooltip title="管理VIP状态">
            <Button size="small" icon={<CrownOutlined />} onClick={() => showVipModal(record)} />
          </Tooltip>
          <Popconfirm
            title={`确定要删除用户 ${record.username} 吗？此操作不可撤销。`}
            onConfirm={() => handleDeleteUser(record.id, record.username)}
            okText="确定删除"
            cancelText="取消"
            icon={<QuestionCircleOutlined style={{ color: 'red' }} />}
            disabled={record.role === 'super_admin'} // Prevent deleting super_admin easily from UI
          >
            <Tooltip title={record.role === 'super_admin' ? "无法删除超级管理员" : "删除用户"}>
              <Button size="small" icon={<DeleteOutlined />} danger disabled={record.role === 'super_admin'} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const UserFilterForm = (
    <Form 
        form={filterForm} 
        layout="inline" 
        onFinish={onFilterSubmit} 
        style={{ marginBottom: 16 }}
    >
        <Form.Item name="username">
            <Input prefix={<SearchOutlined />} placeholder="用户名" allowClear />
        </Form.Item>
        <Form.Item name="email">
            <Input prefix={<SearchOutlined />} placeholder="邮箱" allowClear />
        </Form.Item>
        <Form.Item name="role">
            <Select placeholder="角色" allowClear style={{width: 120}}>
                <Option value="super_admin">超级管理员</Option>
                <Option value="parent_user">父账户</Option>
                <Option value="sub_account">子账户</Option>
                <Option value="developer">开发者</Option>
            </Select>
        </Form.Item>
        <Form.Item name="status">
            <Select placeholder="状态" allowClear style={{width: 120}}>
                <Option value="active">Active</Option>
                <Option value="inactive">Inactive</Option>
                <Option value="suspended">Suspended</Option>
            </Select>
        </Form.Item>
        <Form.Item>
            <Button type="primary" htmlType="submit" icon={<FilterOutlined />}>筛选</Button>
        </Form.Item>
        <Form.Item>
            <Button onClick={() => { filterForm.resetFields(); setFilters({}); setPagination(prev => ({...prev, current: 1})); fetchUsers({page: 1}); }} icon={<ReloadOutlined />}>重置</Button>
        </Form.Item>
    </Form>
  );

  return (
    <Card>
      <Title level={3} style={{ marginBottom: '20px' }}>用户管理 (管理员)</Title>
      <Space style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={showCreateModal}
        >
          创建新用户
        </Button>
      </Space>
      {UserFilterForm}
      <Table 
        columns={userColumns} 
        dataSource={users}
        rowKey="id" 
        pagination={pagination}
        loading={loading} 
        onChange={handleTableChange} // For server-side pagination, sorting, filtering
        scroll={{ x: 'max-content' }} 
      />

      {/* Create User Modal */}
      <Modal
        title="创建新用户"
        visible={isCreateModalVisible}
        onCancel={() => setIsCreateModalVisible(false)}
        footer={null}
        destroyOnClose
        width={600}
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreateUser}>
          <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名!' }, {min: 3}]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, message: '请输入邮箱地址!' }, { type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码!' }, {min: 6}]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请选择用户角色!' }]}>
            <Select placeholder="选择角色">
                <Option value="parent_user">父账户</Option>
                <Option value="sub_account">子账户</Option>
                <Option value="developer">开发者</Option>
                <Option value="super_admin">超级管理员</Option>
            </Select>
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select>
                <Option value="active">Active</Option>
                <Option value="inactive">Inactive</Option>
                <Option value="suspended">Suspended</Option>
            </Select>
          </Form.Item>
           {/* Conditional field for parent_user_id if role is sub_account */}
           <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.role !== currentValues.role}
            >
            {({ getFieldValue }) =>
                getFieldValue('role') === 'sub_account' ? (
                <Form.Item name="parent_user_id" label="父账户ID" rules={[{ required: true, message: '子账户必须指定父账户ID!' }]}>
                    <InputNumber style={{width: '100%'}} placeholder="输入父账户的用户ID" />
                </Form.Item>
                ) : null
            }
            </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              确认创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit User Modal */}
      {editingRecord && (
        <Modal
          title={`编辑用户: ${editingRecord.username}`}
          visible={isEditModalVisible}
          onCancel={() => setIsEditModalVisible(false)}
          footer={null}
          destroyOnClose
          width={600}
        >
          <Form form={editForm} layout="vertical" onFinish={handleEditUser} initialValues={editingRecord}>
            <Form.Item name="username" label="用户名 (不可修改)">
                <Input disabled />
            </Form.Item>
            <Form.Item name="email" label="邮箱" rules={[{ type: 'email' }]}>
                <Input />
            </Form.Item>
            <Form.Item name="role" label="角色" rules={[{ required: true, message: '请选择用户角色!' }]}>
                <Select placeholder="选择角色">
                    <Option value="parent_user">父账户</Option>
                    <Option value="sub_account">子账户</Option>
                    <Option value="developer">开发者</Option>
                    <Option value="super_admin">超级管理员</Option>
                </Select>
            </Form.Item>
            <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择用户状态!' }]}>
                <Select>
                    <Option value="active">Active</Option>
                    <Option value="inactive">Inactive</Option>
                    <Option value="suspended">Suspended</Option>
                </Select>
            </Form.Item>
            {/* Add parent_user_id if role is sub_account and it's editable */}
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                保存更改
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      )}

      {/* VIP Status Modal */}
      {editingRecord && (
        <Modal
          title={`管理用户 ${editingRecord.username} 的VIP状态`}
          visible={isVipModalVisible}
          onCancel={() => setIsVipModalVisible(false)}
          footer={null}
          destroyOnClose
        >
          <Form form={vipForm} layout="vertical" onFinish={handleUpdateVipStatus}>
            <Form.Item name="vip_level_id" label="VIP 等级" rules={[{ required: true, message: '请选择VIP等级!' }]}>
                <Select placeholder="选择VIP等级">
                    {vipLevels.map(level => (
                        <Option key={level.id} value={level.id}>{level.name}</Option>
                    ))}
                </Select>
            </Form.Item>
            <Form.Item name="vip_expiry_date" label="VIP 到期日期">
                <DatePicker style={{width: '100%'}} showTime format="YYYY-MM-DD HH:mm:ss" placeholder="选择到期日期和时间" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                更新VIP状态
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      )}

    </Card>
  );
};

export default AdminUsersPage; 