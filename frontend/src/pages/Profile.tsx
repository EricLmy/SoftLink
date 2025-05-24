import React from 'react';
import { Card, Descriptions } from 'antd';

const Profile: React.FC<{ user: any }> = ({ user }) => {
  if (!user) return null;
  return (
    <Card title="个人中心" style={{ maxWidth: 500, margin: '40px auto' }}>
      <Descriptions column={1} bordered>
        <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
        <Descriptions.Item label="角色">{user.role}</Descriptions.Item>
        <Descriptions.Item label="状态">{user.status === 1 ? '正常' : '禁用'}</Descriptions.Item>
        <Descriptions.Item label="商家ID">{user.merchant_id}</Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default Profile; 