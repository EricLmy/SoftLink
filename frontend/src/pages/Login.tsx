import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, message, Card, Typography } from 'antd';
import { LockOutlined, MailOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;

const Login: React.FC<{ onLogin: (token: string, user: any) => void }> = ({ onLogin }) => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/auth/login', values);
      message.success('登录成功');
      onLogin(res.data.access_token, res.data.user);
      navigate('/'); // 登录成功后跳转主页
    } catch (e: any) {
      message.error(e?.response?.data?.msg || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
        position: 'relative',
      }}
    >
      <Card
        style={{
          width: 380,
          borderRadius: 16,
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.25)',
          background: 'rgba(255,255,255,0.95)',
          border: 'none',
          zIndex: 2,
        }}
        bodyStyle={{ padding: 32 }}
      >
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32, color: '#1e3c72', letterSpacing: 2 }}>
          欢迎登录库存管理系统
        </Title>
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}> 
            <Input prefix={<MailOutlined style={{ color: '#2a5298' }} />} placeholder="请输入邮箱" size="large" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}> 
            <Input.Password prefix={<LockOutlined style={{ color: '#2a5298' }} />} placeholder="请输入密码" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading} size="large" style={{
              background: 'linear-gradient(90deg, #1e3c72 0%, #2a5298 100%)',
              border: 'none',
              borderRadius: 8,
              fontWeight: 600,
              letterSpacing: 2,
              boxShadow: '0 2px 8px rgba(30,60,114,0.10)'
            }}>
              登录
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          没有账号？<Link to="/register">立即注册</Link>
        </div>
      </Card>
      <div
        style={{
          position: 'fixed',
          bottom: 24,
          width: '100%',
          textAlign: 'center',
          color: '#fff',
          opacity: 0.7,
          fontSize: 14,
          zIndex: 1,
          left: 0
        }}
      >
        © 2024 某某公司 版权所有
      </div>
    </div>
  );
};

export default Login; 