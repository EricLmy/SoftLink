import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Table, Button, Modal, Form, Select, message, Typography, Space, Tag, Input, Card, Row, Col, DatePicker, Tooltip, Divider
} from 'antd';
import {
  EyeOutlined, EditOutlined, FilterOutlined, ReloadOutlined, DeleteOutlined
} from '@ant-design/icons';
import { feedbackService } from '../services/api'; // Assuming feedbackService handles admin feedback operations
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// 节流函数，限制函数调用频率
const throttle = (fn, delay) => {
  let lastCall = 0;
  return function (...args) {
    const now = new Date().getTime();
    if (now - lastCall < delay) {
      return;
    }
    lastCall = now;
    return fn(...args);
  };
};

const AdminFeedbackPage = () => {
  const [feedbackList, setFeedbackList] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [sorter, setSorter] = useState({ field: 'submitted_at', order: 'descend' });

  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState(null);
  
  const [form] = Form.useForm(); // For editing feedback status
  const [filterForm] = Form.useForm();

  // 使用ref记录是否已经显示过模拟数据消息
  const hasShownMockMessage = useRef(false);
  // 使用ref存储上次请求的时间，用于节流
  const lastFetchTime = useRef(0);

  const feedbackStatusOptions = [
    { value: 'pending', label: '待处理', color: 'orange' },
    { value: 'processing', label: '处理中', color: 'blue' },
    { value: 'resolved', label: '已解决', color: 'green' },
    { value: 'closed', label: '已关闭', color: 'red' },
  ];

  const fetchInProgress = useRef(false);
  const abortControllerRef = useRef(new AbortController());
  
  // 不使用useCallback的fetchFeedback实现
  const fetchFeedbackImpl = async (params = {}) => {
    // 实现节流，500ms内不重复请求
    const now = Date.now();
    if (now - lastFetchTime.current < 500) {
      return;
    }
    lastFetchTime.current = now;
    
    // 如果已经在请求中，中止上一个请求并开始新请求
    if (fetchInProgress.current) {
      abortControllerRef.current.abort(); // 中止上一个请求
      abortControllerRef.current = new AbortController(); // 创建新的控制器
    }
    
    fetchInProgress.current = true;
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
      
      // 调用获取反馈列表API，可能会返回模拟数据
      const response = await feedbackService.adminGetFeedbacks(queryParams);
      
      // 判断是否是模拟数据
      const isMockData = response.data.feedbacks && response.data.feedbacks.length > 0 && 
                         response.data.feedbacks[0].id === 1 && 
                         response.data.feedbacks[0].user.username === '测试用户1';
      
      if (isMockData && !hasShownMockMessage.current) {
        // 使用key确保消息只显示一次
        message.info({
          content: '当前显示的是模拟数据，后端API尚未实现。',
          key: 'mock-data-message',
          duration: 3
        });
        hasShownMockMessage.current = true; // 标记已经显示过消息
      }
      
      // 设置反馈列表数据
      setFeedbackList(response.data.feedbacks || response.data.items || response.data || []);
      
      // 设置分页信息
      setPagination(prev => ({ 
        ...prev, 
        total: response.data.total || response.data.total_items || response.data.length || 0 
      })); 
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('请求被中止');
        return; // 中止的请求不需要处理
      }
      
      console.error("获取用户反馈列表失败:", error);
      
      // 错误处理 - 理论上不应该进入这里，因为我们添加了模拟数据作为fallback
      // 但出于稳健性考虑，仍保留错误处理
      if (error.response?.status === 404) {
        message.warning({
          content: '用户反馈管理功能尚未完全实现，请稍后再试。',
          key: 'api-error-message'
        });
      } else if (error.response?.status === 403) {
        message.error({
          content: '您没有权限查看用户反馈列表。',
          key: 'permission-error-message'
        });
      } else {
        message.error({
          content: '获取用户反馈列表失败，请稍后重试。',
          key: 'general-error-message'
        });
      }
      
      setFeedbackList([]);
    } finally {
      setLoading(false);
      fetchInProgress.current = false;
    }
  };

  // 使用ref存储当前的fetchFeedbackImpl函数
  const fetchFeedbackRef = useRef(fetchFeedbackImpl);
  
  // 在依赖项变化时更新ref
  useEffect(() => {
    fetchFeedbackRef.current = fetchFeedbackImpl;
  }, [filters, sorter, pagination]);
  
  // 公开的安全fetchFeedback函数
  const fetchFeedback = useCallback((params = {}) => {
    fetchFeedbackRef.current(params);
  }, []);

  useEffect(() => {
    // 初始加载数据
    fetchFeedback();
    
    // 组件卸载时中止请求
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchFeedback]);

  const handleTableChange = (newPagination, newFilters, newSorter) => {
    setSorter(newSorter.field ? { field: newSorter.field, order: newSorter.order } : {});
    // Filters from table are not directly used, using filterForm instead
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize })); 
  };

  const onFilterSubmit = (values) => {
    const newFilters = { ...values };
    if (newFilters.submitted_at_range && newFilters.submitted_at_range.length === 2) {
      newFilters.start_date = newFilters.submitted_at_range[0].format('YYYY-MM-DD');
      newFilters.end_date = newFilters.submitted_at_range[1].format('YYYY-MM-DD');
    }
    delete newFilters.submitted_at_range;
    
    const activeFilters = Object.fromEntries(Object.entries(newFilters).filter(([_, v]) => v !== undefined && v !== ''));
    setFilters(activeFilters);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const showViewModal = (feedback) => {
    setSelectedFeedback(feedback);
    setIsViewModalVisible(true);
  };

  const showEditModal = (feedback) => {
    setSelectedFeedback(feedback);
    form.setFieldsValue({
      status: feedback.status,
      resolution_notes: feedback.resolution_notes || '' // Assuming a field for admin notes
    });
    setIsEditModalVisible(true);
  };

  const handleEditSubmit = async (values) => {
    if (!selectedFeedback) return;
    setLoading(true);
    try {
      // 使用正确的方法名更新反馈状态，并传递resolution_notes
      const response = await feedbackService.adminUpdateFeedbackStatus(
        selectedFeedback.id, 
        values.status, 
        values.resolution_notes
      );
      
      // 检查是否是模拟响应
      if (response.data.message && response.data.message.includes('模拟数据')) {
        message.info({
          content: '当前使用模拟数据，状态更新仅作为界面演示。',
          key: 'update-mock-message'
        });
      } else {
        message.success({
          content: '反馈状态更新成功！',
          key: 'update-success-message'
        });
      }
      
      setIsEditModalVisible(false);
      
      // 如果处理的是模拟数据，手动更新列表中的状态
      if (selectedFeedback.id <= 3) {
        setFeedbackList(prev => prev.map(item => 
          item.id === selectedFeedback.id 
            ? { 
                ...item, 
                status: values.status, 
                resolution_notes: values.resolution_notes,
                resolved_at: values.status === 'resolved' ? new Date().toISOString() : item.resolved_at,
                resolver: { username: '当前管理员' },
                resolver_id: 9999
              } 
            : item
        ));
      } else {
        // 否则刷新列表
        fetchFeedback({ page: pagination.current });
      }
    } catch (error) {
      console.error("更新反馈状态失败:", error);
      
      if (error.response?.status === 404) {
        message.warning({
          content: '反馈管理功能尚未完全实现，请稍后再试。',
          key: 'update-api-error-message'
        });
      } else {
        message.error({
          content: error.response?.data?.message || '更新反馈状态失败。',
          key: 'update-error-message'
        });
      }
    }
    setLoading(false);
  };

  const getStatusTag = (status) => {
    const statusObj = feedbackStatusOptions.find(s => s.value === status);
    return statusObj ? <Tag color={statusObj.color}>{statusObj.label}</Tag> : <Tag>{status}</Tag>;
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: true, width: 80 },
    {
      title: '用户',
      dataIndex: ['user', 'username'], 
      key: 'username',
      render: (username, record) => username || (record.user_id ? `User ID: ${record.user_id}` : '匿名'),
      sorter: true,
    },
    { title: '分类', dataIndex: 'category', key: 'category', sorter: true, render: cat => cat || '-' },
    {
      title: '内容摘要',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => <Tooltip title={text}>{text}</Tooltip>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: getStatusTag,
      sorter: true,
      filters: feedbackStatusOptions.map(s => ({ text: s.label, value: s.value })),
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '提交时间',
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      render: (text) => moment(text).format('YYYY-MM-DD HH:mm'),
      sorter: true,
      defaultSortOrder: 'descend',
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button size="small" icon={<EyeOutlined />} onClick={() => showViewModal(record)} />
          </Tooltip>
          <Tooltip title="处理反馈">
            <Button size="small" icon={<EditOutlined />} onClick={() => showEditModal(record)} />
          </Tooltip>
          <Tooltip title="删除反馈">
            <Button 
              size="small" 
              danger
              icon={<DeleteOutlined />} 
              onClick={() => {
                Modal.confirm({
                  title: '确认删除',
                  content: '确定要删除这条反馈吗？此操作不可撤销。',
                  okText: '确认',
                  okType: 'danger',
                  cancelText: '取消',
                  onOk: () => handleDelete(record.id)
                });
              }} 
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const handleDelete = async (id) => {
    setLoading(true);
    try {
      const response = await feedbackService.adminDeleteFeedback(id);
      
      // 检查是否是模拟响应
      if (response.data.message && response.data.message.includes('模拟数据')) {
        message.info({
          content: '当前使用模拟数据，删除操作仅作为界面演示。',
          key: 'delete-mock-message'
        });
      } else {
        message.success({
          content: '反馈删除成功！',
          key: 'delete-success-message'
        });
      }
      
      // 如果删除的是模拟数据，手动从列表中移除
      if (id <= 3) {
        setFeedbackList(prev => prev.filter(item => item.id !== id));
        
        // 更新总数以保持分页一致
        setPagination(prev => ({
          ...prev,
          total: prev.total - 1
        }));
      } else {
        // 如果删除的是最后一条数据且不是第一页，则前往上一页
        if (feedbackList.length === 1 && pagination.current > 1) {
          fetchFeedback({ page: pagination.current - 1 });
        } else {
          fetchFeedback({ page: pagination.current });
        }
      }
    } catch (error) {
      console.error("删除反馈失败:", error);
      
      if (error.response?.status === 404) {
        message.warning({
          content: '反馈管理功能尚未完全实现，请稍后再试。',
          key: 'delete-api-error-message'
        });
      } else if (error.response?.status === 403) {
        message.error({
          content: '您没有权限删除反馈。',
          key: 'delete-permission-error-message'
        });
      } else {
        message.error({
          content: error.response?.data?.message || '删除反馈失败。',
          key: 'delete-error-message'
        });
      }
    }
    setLoading(false);
  };

  return (
    <Card>
      <Title level={3} style={{ marginBottom: '20px' }}>用户反馈查阅</Title>
      
      <Form form={filterForm} layout="inline" onFinish={onFilterSubmit} style={{ marginBottom: 16 }}>
        <Form.Item name="user_query" label="用户/内容">
          <Input placeholder="搜索用户名或内容关键字" allowClear />
        </Form.Item>
        <Form.Item name="status" label="状态">
          <Select placeholder="筛选状态" allowClear style={{ width: 120 }}>
            {feedbackStatusOptions.map(opt => <Option key={opt.value} value={opt.value}>{opt.label}</Option>)}
          </Select>
        </Form.Item>
        <Form.Item name="category" label="分类">
          <Input placeholder="筛选分类" allowClear />
        </Form.Item>
        <Form.Item name="submitted_at_range" label="提交日期">
            <DatePicker.RangePicker />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<FilterOutlined />}>筛选</Button>
        </Form.Item>
        <Form.Item>
          <Button onClick={() => { filterForm.resetFields(); onFilterSubmit({}); fetchFeedback({page: 1}); }} icon={<ReloadOutlined />}>重置</Button>
        </Form.Item>
      </Form>

      <Table 
        columns={columns} 
        dataSource={feedbackList}
        rowKey="id" 
        pagination={pagination}
        loading={loading}
        onChange={handleTableChange}
        scroll={{ x: 'max-content' }}
        locale={{
          emptyText: loading ? (
            '加载中...'
          ) : (
            <div style={{ padding: '24px 0' }}>
              <p>暂无反馈数据</p>
            </div>
          )
        }}
      />

      <Modal
        title="反馈详情"
        visible={isViewModalVisible}
        onCancel={() => setIsViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsViewModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="edit" 
            type="primary" 
            onClick={() => {
              setIsViewModalVisible(false);
              showEditModal(selectedFeedback);
            }}
          >
            处理
          </Button>
        ]}
        width={700}
      >
        {selectedFeedback && (
          <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Text strong>反馈ID：</Text> {selectedFeedback.id}
              </Col>
              <Col span={12}>
                <Text strong>状态：</Text> {getStatusTag(selectedFeedback.status)}
              </Col>
              <Col span={12}>
                <Text strong>用户：</Text> {selectedFeedback.user?.username || '匿名'}
              </Col>
              <Col span={12}>
                <Text strong>分类：</Text> {selectedFeedback.category || '-'}
              </Col>
              <Col span={24}>
                <Text strong>提交时间：</Text> {moment(selectedFeedback.submitted_at).format('YYYY-MM-DD HH:mm:ss')}
              </Col>
              <Col span={24}>
                <Text strong>反馈内容：</Text>
                <div style={{ 
                  border: '1px solid #f0f0f0', 
                  borderRadius: '4px', 
                  padding: '12px', 
                  marginTop: '8px',
                  backgroundColor: '#fafafa',
                  whiteSpace: 'pre-wrap',
                  minHeight: '100px'
                }}>
                  {selectedFeedback.content}
                </div>
              </Col>
              
              {(selectedFeedback.status === 'resolved' || selectedFeedback.status === 'closed') && (
                <>
                  <Col span={24}>
                    <Divider orientation="left">处理信息</Divider>
                  </Col>
                  <Col span={12}>
                    <Text strong>处理人：</Text> {selectedFeedback.resolver?.username || '-'}
                  </Col>
                  <Col span={12}>
                    <Text strong>处理时间：</Text> {selectedFeedback.resolved_at ? moment(selectedFeedback.resolved_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                  </Col>
                  <Col span={24}>
                    <Text strong>处理结果：</Text>
                    <div style={{ 
                      border: '1px solid #f0f0f0', 
                      borderRadius: '4px', 
                      padding: '12px', 
                      marginTop: '8px',
                      backgroundColor: '#fafafa',
                      whiteSpace: 'pre-wrap',
                      minHeight: '60px'
                    }}>
                      {selectedFeedback.resolution_notes || '无备注'}
                    </div>
                  </Col>
                </>
              )}
            </Row>
          </div>
        )}
      </Modal>

      <Modal
        title="处理反馈"
        visible={isEditModalVisible}
        onCancel={() => setIsEditModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedFeedback && (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleEditSubmit}
          >
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Text strong>反馈内容：</Text>
                <div style={{ 
                  border: '1px solid #f0f0f0', 
                  borderRadius: '4px', 
                  padding: '12px', 
                  marginTop: '8px',
                  marginBottom: '16px',
                  backgroundColor: '#fafafa',
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedFeedback.content}
                </div>
              </Col>
            </Row>
            
            <Form.Item
              name="status"
              label="状态"
              rules={[{ required: true, message: '请选择处理状态!' }]}
            >
              <Select>
                {feedbackStatusOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>
                    <Tag color={opt.color} style={{ marginRight: 8 }}>{opt.label}</Tag>
                  </Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item
              name="resolution_notes"
              label="处理备注"
              rules={[
                { required: form.getFieldValue('status') === 'resolved' || form.getFieldValue('status') === 'closed', 
                  message: '请填写处理结果!' }
              ]}
            >
              <TextArea
                rows={4}
                placeholder="请输入处理结果或备注信息..."
              />
            </Form.Item>
            
            <Form.Item>
              <Row justify="end" gutter={16}>
                <Col>
                  <Button onClick={() => setIsEditModalVisible(false)}>
                    取消
                  </Button>
                </Col>
                <Col>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    提交
                  </Button>
                </Col>
              </Row>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </Card>
  );
};

export default AdminFeedbackPage; 