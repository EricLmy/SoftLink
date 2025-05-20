import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, message, Descriptions, Row, Col, Spin, Space } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { userService } from '../services/api'; // Assuming userService has getProfile and updateProfile (or changePassword)

const { Title } = Typography;

const UserProfilePage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setProfileLoading(true);
      try {
        const response = await userService.getProfile();
        setCurrentUser(response.data);
      } catch (error) {
        message.error('无法加载您的个人信息，请稍后重试。');
        console.error("Failed to fetch profile:", error);
      }
      setProfileLoading(false);
    };
    fetchProfile();
  }, []);

  const handleChangePassword = async (values) => {
    setLoading(true);
    try {
      // Assuming your userService.updateProfile can handle password changes
      // or you have a specific changePassword method.
      // The backend /api/users/me (PUT) needs to handle 'old_password', 'new_password' fields.
      await userService.updateProfile({ 
        current_password: values.oldPassword, // Or 'old_password' based on backend API
        password: values.newPassword 
      });
      message.success('密码修改成功！');
      form.resetFields([
        'oldPassword',
        'newPassword',
        'confirmNewPassword'
      ]);
    } catch (error) {
      message.error(error.response?.data?.message || '密码修改失败，请检查您的旧密码是否正确或稍后重试。');
      console.error("Failed to change password:", error);
    }
    setLoading(false);
  };

  if (profileLoading) {
    return <Row justify="center" align="middle" style={{minHeight: '200px'}}><Spin tip="加载个人信息中..." /></Row>;
  }

  if (!currentUser) {
    return <Row justify="center" align="middle" style={{minHeight: '200px'}}><Typography.Text type="danger">无法加载用户信息。</Typography.Text></Row>;
  }

  return (
    <Row justify="center" style={{ marginTop: '20px' }}>
      <Col xs={24} sm={20} md={16} lg={12} xl={10}>
        <Card style={{ marginBottom: '24px' }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>个人信息</Title>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label={<Space><UserOutlined />用户名</Space>}>{currentUser.username}</Descriptions.Item>
            <Descriptions.Item label={<Space><MailOutlined />邮箱</Space>}>{currentUser.email}</Descriptions.Item>
            <Descriptions.Item label="角色">{currentUser.role}</Descriptions.Item>
            {currentUser.vip_level_name && (
              <Descriptions.Item label="VIP等级">{currentUser.vip_level_name}</Descriptions.Item>
            )}
            {currentUser.vip_expiry_date && (
              <Descriptions.Item label="VIP到期时间">{new Date(currentUser.vip_expiry_date).toLocaleDateString()}</Descriptions.Item>
            )}
             <Descriptions.Item label="上次登录时间">{currentUser.last_login_at ? new Date(currentUser.last_login_at).toLocaleString() : 'N/A'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card>
          <Title level={4} style={{ textAlign: 'center', marginBottom: '24px' }}>修改密码</Title>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleChangePassword}
            name="changePasswordForm"
          >
            <Form.Item
              name="oldPassword"
              label="当前密码"
              rules={[
                { required: true, message: '请输入您的当前密码!' },
              ]}
              hasFeedback
            >
              <Input.Password prefix={<LockOutlined />} placeholder="当前密码" />
            </Form.Item>

            <Form.Item
              name="newPassword"
              label="新密码"
              rules={[
                { required: true, message: '请输入您的新密码!' },
                { min: 6, message: '密码至少为6个字符!' },
              ]}
              hasFeedback
            >
              <Input.Password prefix={<LockOutlined />} placeholder="新密码" />
            </Form.Item>

            <Form.Item
              name="confirmNewPassword"
              label="确认新密码"
              dependencies={['newPassword']}
              hasFeedback
              rules={[
                { required: true, message: '请确认您的新密码!' },
                ({
                  validator(_, value) {
                    if (!value || form.getFieldValue('newPassword') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的密码不一致!'));
                  },
                }),
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="确认新密码" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                确认修改密码
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Col>
    </Row>
  );
};

export default UserProfilePage; 