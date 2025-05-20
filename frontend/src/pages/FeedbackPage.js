import React, { useState } from 'react';
import { Form, Input, Button, Select, message, Typography, Card, Row, Col, Alert } from 'antd';
import { feedbackService } from '../services/api';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const FeedbackPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (values) => {
    setLoading(true);
    setError(null);

    try {
      // 直接传入整个values对象
      const response = await feedbackService.submitFeedback(values);
      message.success(response.data?.message || '反馈已成功提交！感谢您的宝贵意见。');
      form.resetFields();
    } catch (error) {
      console.error("提交反馈失败:", error);
      
      if (error.response?.data?.errors) {
        // 处理验证错误
        const validationErrors = error.response.data.errors;
        const errorMessages = [];
        
        for (const field in validationErrors) {
          errorMessages.push(`${field}: ${validationErrors[field].join(', ')}`);
        }
        
        setError(errorMessages.join('\n'));
      } else {
        setError(error.response?.data?.message || '提交反馈失败，请稍后重试。');
      }
      
      message.error('提交失败，请检查表单内容。');
    }
    
    setLoading(false);
  };

  return (
    <Row justify="center" style={{ marginTop: '20px' }}>
      <Col xs={24} sm={20} md={16} lg={12} xl={10}>
        <Card>
          <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>用户意见反馈</Title>
          
          {error && (
            <Alert
              message="提交错误"
              description={error}
              type="error"
              showIcon
              closable
              style={{ marginBottom: 24 }}
              onClose={() => setError(null)}
            />
          )}
          
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ category: 'general' }} // Default category
          >
            <Form.Item
              name="category"
              label={<span className="required-field">反馈类别</span>}
              rules={[{ required: true, message: '请选择反馈类别!' }]}
            >
              <Select placeholder="选择一个类别">
                <Option value="general">常规问题</Option>
                <Option value="bug">Bug报告</Option>
                <Option value="feature_request">功能建议</Option>
                <Option value="improvement">改进意见</Option>
                <Option value="other">其他</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="content"
              label={<span className="required-field">反馈内容</span>}
              rules={[
                { required: true, message: '请输入反馈内容!' },
                { min: 2, message: '反馈内容至少2个字符' },
                { max: 1000, message: '反馈内容不能超过1000个字符' }
              ]}
            >
              <TextArea 
                rows={6} 
                placeholder="请详细描述您的问题或建议..." 
                showCount 
                maxLength={1000}
              />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                提交反馈
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Col>
    </Row>
  );
};

export default FeedbackPage; 