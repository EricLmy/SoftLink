import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, message, Typography, Space, Popconfirm, Spin, Tag, Tooltip, Card } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, HistoryOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { userService } from '../services/api'; // Ensure userService has methods for sub-accounts

const { Title, Text } = Typography;

const SubAccountsPage = () => {
  const [subAccounts, setSubAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [isLogsModalVisible, setIsLogsModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [activityLogs, setActivityLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [selectedSubAccountForLogs, setSelectedSubAccountForLogs] = useState(null);

  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const fetchSubAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await userService.getSubAccounts(); // GET /users/me/sub-accounts
      setSubAccounts(response.data.sub_accounts || response.data || []); // Adjust based on actual API response structure
    } catch (error) {
      console.error("获取子账户列表失败:", error);
      
      // 检查是否是后端API未实现的错误
      if (error.response?.status === 404) {
        message.warning('子账户管理功能尚未完全实现，请稍后再试。');
      } else if (error.response?.status === 403) {
        message.error('您没有权限访问子账户列表。');
      } else {
        message.error('获取子账户列表失败，请稍后重试。');
      }
      
      // 即使API失败，也设置一个空数组避免UI错误
      setSubAccounts([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSubAccounts();
  }, [fetchSubAccounts]);

  // --- Create Sub-Account Handlers ---
  const showCreateModal = () => {
    createForm.resetFields();
    setIsCreateModalVisible(true);
  };

  const handleCreateSubAccount = async (values) => {
    setLoading(true);
    try {
      await userService.createSubAccount(values); // POST /users/me/sub-accounts
      message.success('子账户创建成功！');
      setIsCreateModalVisible(false);
      fetchSubAccounts(); // Refresh list
    } catch (error) {
      console.error("创建子账户失败:", error);
      
      if (error.response?.status === 409) {
        message.error('用户名或邮箱已存在，请更换后重试。');
      } else if (error.response?.status === 403) {
        message.error('您没有权限创建子账户。');
      } else if (error.response?.status === 404) {
        message.warning('子账户管理功能尚未完全实现，请稍后再试。');
      } else {
        message.error(error.response?.data?.message || '子账户创建失败。');
      }
    }
    setLoading(false);
  };

  // --- Edit Sub-Account (Reset Password) Handlers ---
  const showEditModal = (record) => {
    setEditingRecord(record);
    editForm.setFieldsValue({ username: record.username }); // Display username, password field will be for new pass
    editForm.resetFields(['password']);
    setIsEditModalVisible(true);
  };

  const handleEditSubAccount = async (values) => {
    setLoading(true);
    try {
      // API should allow updating password for a sub-account
      await userService.updateSubAccount(editingRecord.id, { password: values.password }); // PUT /users/me/sub-accounts/{id}
      message.success(`子账户 ${editingRecord.username} 的密码已重置。`);
      setIsEditModalVisible(false);
      fetchSubAccounts();
    } catch (error) {
      console.error("重置密码失败:", error);
      
      if (error.response?.status === 403) {
        message.error('您没有权限修改此子账户。');
      } else if (error.response?.status === 404) {
        message.error('子账户不存在或功能尚未实现。');
      } else {
        message.error(error.response?.data?.message || '密码重置失败。');
      }
    }
    setLoading(false);
  };
  
  // --- Delete Sub-Account Handler ---
  const handleDeleteSubAccount = async (subAccountId, username) => {
    setLoading(true);
    try {
      await userService.deleteSubAccount(subAccountId); // DELETE /users/me/sub-accounts/{id}
      message.success(`子账户 ${username} 已成功删除。`);
      fetchSubAccounts();
    } catch (error) {
      console.error("删除子账户失败:", error);
      
      if (error.response?.status === 403) {
        message.error('您没有权限删除此子账户。');
      } else if (error.response?.status === 404) {
        message.error('子账户不存在或已被删除。');
      } else {
        message.error(error.response?.data?.message || '删除子账户失败。');
      }
    }
    setLoading(false);
  };

  // --- Activity Logs Handlers ---
  const showLogsModal = async (record) => {
    setSelectedSubAccountForLogs(record);
    setIsLogsModalVisible(true);
    setLogsLoading(true);
    try {
      // 获取子账户活动日志
      const response = await userService.getSubAccountActivityLogs(record.id, 1, 100);
      setActivityLogs(response.data.logs || response.data || []);
    } catch (error) {
      console.error("获取活动日志失败:", error);
      
      if (error.response?.status === 404) {
        message.warning('活动日志功能尚未实现，请稍后再试。');
      } else if (error.response?.status === 403) {
        message.error('您没有权限查看此子账户的活动日志。');
      } else {
        message.error('获取活动日志失败，请稍后重试。');
      }
      
      // 设置空数组以避免UI渲染错误
      setActivityLogs([]);
    }
    setLogsLoading(false);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: (a, b) => a.id - b.id },
    { title: '用户名', dataIndex: 'username', key: 'username', sorter: (a, b) => a.username.localeCompare(b.username) },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: status => (
        <Tag color={status === 'active' ? 'green' : 'volcano'}>{status ? status.toUpperCase() : 'N/A'}</Tag>
      )
    },
    { title: '创建日期', dataIndex: 'created_at', key: 'created_at', render: (text) => text ? new Date(text).toLocaleDateString() : 'N/A' },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Tooltip title="重置密码">
            <Button icon={<EditOutlined />} onClick={() => showEditModal(record)} />
          </Tooltip>
          <Tooltip title="查看活动日志">
            <Button icon={<HistoryOutlined />} onClick={() => showLogsModal(record)} />
          </Tooltip>
          <Popconfirm
            title={`确定要删除子账户 ${record.username} 吗？此操作不可撤销。`}
            onConfirm={() => handleDeleteSubAccount(record.id, record.username)}
            okText="确定删除"
            cancelText="取消"
            icon={<QuestionCircleOutlined style={{ color: 'red' }} />}
          >
            <Button icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const logColumns = [
    { title: '时间', dataIndex: 'timestamp', key: 'timestamp', render: (text) => new Date(text).toLocaleString(), width: 180 },
    { title: '操作IP', dataIndex: 'ip_address', key: 'ip_address', width: 130 },
    { title: '动作', dataIndex: 'action', key: 'action', width: 150 },
    { title: '详情', dataIndex: 'details', key: 'details', render: (details) => <pre style={{whiteSpace: 'pre-wrap', wordBreak: 'break-all'}}>{typeof details === 'object' ? JSON.stringify(details, null, 2) : details}</pre> },
  ];


  return (
    <Card>
      <Title level={3} style={{ marginBottom: '20px' }}>子账户管理</Title>
      <Button 
        type="primary" 
        icon={<PlusOutlined />} 
        onClick={showCreateModal} 
        style={{ marginBottom: 16 }}
      >
        创建子账户
      </Button>
      <Table 
        columns={columns} 
        dataSource={subAccounts}
        loading={loading} 
        rowKey="id" 
        scroll={{ x: 'max-content' }}
        locale={{
          emptyText: loading ? '加载中...' : (
            <div style={{ padding: '24px 0' }}>
              <p>暂无子账户数据</p>
              <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
                创建第一个子账户
              </Button>
            </div>
          )
        }}
      />

      {/* Create Sub-Account Modal */}
      <Modal
        title="创建新子账户"
        visible={isCreateModalVisible}
        onCancel={() => setIsCreateModalVisible(false)}
        footer={null} // Using form's submit button
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreateSubAccount}>
          <Form.Item 
            name="username" 
            label="用户名" 
            rules={[{ required: true, message: '请输入用户名!' }, {min: 3, message: '用户名至少3个字符'}]}>
            <Input />
          </Form.Item>
          <Form.Item 
            name="email" 
            label="邮箱" 
            rules={[{ required: true, message: '请输入邮箱地址!' }, { type: 'email', message: '请输入有效的邮箱地址!' }]}>
            <Input />
          </Form.Item>
          <Form.Item 
            name="password" 
            label="初始密码" 
            rules={[{ required: true, message: '请输入初始密码!' }, {min: 6, message: '密码至少6个字符'}]}>
            <Input.Password />
          </Form.Item>
          {/* TODO: Add fields for feature_permissions if backend supports it for Phase 1 */}
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              确认创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Sub-Account (Reset Password) Modal */}
      {editingRecord && (
        <Modal
          title={`重置子账户 ${editingRecord.username} 的密码`}
          visible={isEditModalVisible}
          onCancel={() => setIsEditModalVisible(false)}
          footer={null}
          destroyOnClose
        >
          <Text type="secondary" style={{display: 'block', marginBottom: '10px'}}>为用户 <Tag>{editingRecord.username}</Tag> 设置新密码。</Text>
          <Form form={editForm} layout="vertical" onFinish={handleEditSubAccount}>
            <Form.Item name="username" label="用户名" initialValue={editingRecord.username} hidden>
                <Input disabled />
            </Form.Item>
            <Form.Item 
                name="password" 
                label="新密码" 
                rules={[{ required: true, message: '请输入新密码!' }, {min: 6, message: '密码至少6个字符'}]}>
              <Input.Password placeholder="输入新密码"/>
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                确认重置密码
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      )}

      {/* Activity Logs Modal */}
      {selectedSubAccountForLogs && (
        <Modal
            title={`子账户 ${selectedSubAccountForLogs.username} 的活动日志`}
            visible={isLogsModalVisible}
            onCancel={() => setIsLogsModalVisible(false)}
            footer={[
                <Button key="close" onClick={() => setIsLogsModalVisible(false)}>
                    关闭
                </Button>,
            ]}
            width={800}
            destroyOnClose
        >
            <Spin spinning={logsLoading} tip="加载日志中...">
                <Table
                    columns={logColumns}
                    dataSource={activityLogs}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                    scroll={{ y: 400, x: 'max-content' }}
                    size="small"
                />
            </Spin>
        </Modal>
      )}

    </Card>
  );
};

export default SubAccountsPage; 