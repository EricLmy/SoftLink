import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, message, Card, Typography } from 'antd';
import axios from 'axios';

const { Title } = Typography;

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await axios.post('/api/auth/register', values);
      message.success('注册成功，请登录');
      setTimeout(() => navigate('/login'), 1000);
    } catch (e: any) {
      message.error(e?.response?.data?.msg || '注册失败');
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
          width: 420,
          borderRadius: 16,
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.25)',
          background: 'rgba(255,255,255,0.95)',
          border: 'none',
          zIndex: 2,
        }}
        bodyStyle={{ padding: 32 }}
      >
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32, color: '#1e3c72', letterSpacing: 2 }}>
          注册新账号
        </Title>
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="merchant_name" label="商家名称" rules={[{ required: true, message: '请输入商家名称' }]}> 
            <Input placeholder="请输入商家名称" size="large" />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}> 
            <Input placeholder="请输入邮箱" size="large" />
          </Form.Item>
          <Form.Item name="phone" label="手机号" rules={[{ required: true, pattern: /^1[3-9]\d{9}$/, message: '请输入有效手机号' }]}> 
            <Input placeholder="请输入手机号" size="large" />
          </Form.Item>
          <Form.Item name="username" label="管理员用户名" rules={[{ required: true, message: '请输入管理员用户名' }]}> 
            <Input placeholder="请输入管理员用户名" size="large" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6, message: '密码至少6位' }]}> 
            <Input.Password placeholder="请输入密码" size="large" />
          </Form.Item>
          <Form.Item name="confirm" label="确认密码" dependencies={["password"]} rules={[
            { required: true, message: '请确认密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}>
            <Input.Password placeholder="请再次输入密码" size="large" />
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
              注册
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          已有账号？<Link to="/login">返回登录</Link>
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

export default Register; 