import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, message, Typography, Row, Col, Tabs, Spin } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, LoginOutlined, UserAddOutlined } from '@ant-design/icons';
import { authService } from '../services/api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const LoginPage = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const [showWelcome, setShowWelcome] = useState(true);

  // 组件初次渲染时的欢迎动画
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleLogin = async (values) => {
    setLoading(true);
    try {
      const response = await authService.login(values.username, values.password);
      message.success('登录成功，欢迎回来！');
      onLoginSuccess(response.data.access_token, response.data.user_info);
    } catch (error) {
      message.error(error.response?.data?.message || '登录失败，请检查用户名和密码');
    }
    setLoading(false);
  };

  const handleRegister = async (values) => {
    setLoading(true);
    try {
      console.log('用户注册请求:', values);
      const response = await authService.register(values.username, values.email, values.password);
      console.log('注册成功响应:', response.data);
      message.success('注册成功，请登录！');
      // Optionally auto-login or switch to login tab
      setActiveTab('login'); // Switch to login tab after successful registration
    } catch (error) {
      console.error('注册失败详情:', error);
      
      if (error.response?.status === 400) {
        // 处理验证错误
        if (error.response.data?.errors) {
          const validationErrors = error.response.data.errors;
          for (const field in validationErrors) {
            message.error(`${field}: ${validationErrors[field].join(', ')}`);
          }
        } else {
          message.error(error.response.data?.message || '注册失败：输入数据无效');
        }
      } else if (error.response?.status === 409) {
        // 处理冲突，例如用户名或邮箱已存在
        message.error('用户名或邮箱已被使用，请尝试其他值');
      } else {
        // 处理其他错误
        message.error(error.response?.data?.message || '注册失败，请稍后重试');
      }
    }
    setLoading(false);
  };

  // 欢迎页面动画
  if (showWelcome) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center',
        background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)'
      }}>
        <div style={{ 
          animation: 'fadeIn 1.5s ease-in-out',
          textAlign: 'center'
        }}>
          <Title style={{ color: 'white', fontSize: '48px', marginBottom: '20px' }}>
            牧联 SoftLink
          </Title>
          <Spin size="large" />
        </div>
      </div>
    );
  }

  return (
    <Row justify="center" align="middle" style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e7eb 100%)'
    }}>
      <Col xs={22} sm={16} md={12} lg={8} xl={6}>
        <div style={{ 
          transform: 'translateY(-30px)', 
          opacity: 1, 
          animation: 'fadeInUp 0.8s ease-out forwards',
          transition: 'all 0.3s ease'
        }}>
          <Card className="custom-card" style={{ 
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
            borderRadius: '8px'
          }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <Title level={2} style={{ color: '#1890ff' }}>牧联 SoftLink</Title>
              <Text type="secondary">企业数字化管理解决方案</Text>
            </div>
            <Tabs 
              activeKey={activeTab} 
              onChange={setActiveTab} 
              centered
              animated={{ inkBar: true, tabPane: true }}
            >
              <TabPane 
                tab={<span><LoginOutlined /> 登录</span>} 
                key="login"
              >
                <Form 
                  name="login" 
                  onFinish={handleLogin} 
                  autoComplete="off"
                  layout="vertical"
                  requiredMark={false}
                >
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: '请输入用户名!' }]}
                  >
                    <Input 
                      prefix={<UserOutlined />} 
                      placeholder="用户名"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: '请输入密码!' }]}
                  >
                    <Input.Password 
                      prefix={<LockOutlined />} 
                      placeholder="密码"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button 
                      type="primary" 
                      htmlType="submit" 
                      loading={loading} 
                      block
                      size="large"
                      className="btn-hover-effect"
                    >
                      登录
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>
              <TabPane 
                tab={<span><UserAddOutlined /> 注册</span>} 
                key="register"
              >
                <Form 
                  name="register" 
                  onFinish={handleRegister} 
                  autoComplete="off"
                  layout="vertical"
                  requiredMark={false}
                >
                  <Form.Item
                    name="username"
                    rules={[
                      { required: true, message: '请输入用户名!' }, 
                      { min: 3, message: '用户名至少3位' }
                    ]}
                  >
                    <Input 
                      prefix={<UserOutlined />} 
                      placeholder="用户名" 
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱地址!' }, 
                      { type: 'email', message: '请输入有效的邮箱地址!' }
                    ]}
                  >
                    <Input 
                      prefix={<MailOutlined />} 
                      placeholder="邮箱" 
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: '请输入密码!' }, 
                      { min: 6, message: '密码至少6位' }
                    ]}
                  >
                    <Input.Password 
                      prefix={<LockOutlined />} 
                      placeholder="密码" 
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="confirmPassword"
                    dependencies={['password']}
                    rules={[
                      { required: true, message: '请确认密码!' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('两次输入的密码不一致!'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password 
                      prefix={<LockOutlined />} 
                      placeholder="确认密码" 
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button 
                      type="primary" 
                      htmlType="submit" 
                      loading={loading} 
                      block
                      size="large"
                      className="btn-hover-effect"
                    >
                      注册
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>
            </Tabs>
          </Card>
        </div>
      </Col>
    </Row>
  );
};

export default LoginPage; 