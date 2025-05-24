import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  ShoppingOutlined,
  InboxOutlined,
  SwapOutlined,
  OrderedListOutlined,
  AlertOutlined,
  TeamOutlined,
  UserOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘'
    },
    {
      key: '/product',
      icon: <ShoppingOutlined />,
      label: '商品管理'
    },
    {
      key: '/inventory',
      icon: <InboxOutlined />,
      label: '库存管理'
    },
    {
      key: '/stock-record',
      icon: <SwapOutlined />,
      label: '出入库管理'
    },
    {
      key: '/order',
      icon: <OrderedListOutlined />,
      label: '订单管理'
    },
    {
      key: '/alert',
      icon: <AlertOutlined />,
      label: '告警中心'
    },
    {
      key: '/permission',
      icon: <TeamOutlined />,
      label: '权限管理'
    },
    {
      key: '/profile',
      icon: <UserOutlined />,
      label: '个人中心'
    }
  ];

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sider width={200} breakpoint="lg" collapsedWidth="0">
        <div style={{ height: 32, margin: 16, background: 'rgba(255,255,255,0.3)' }} />
        <Menu 
          theme="dark" 
          mode="inline" 
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <div style={{ flex: 1, background: '#f5f7fa', minWidth: 0 }}>
        <Layout style={{ height: '100%', width: '100%', background: 'transparent' }}>
          <Header style={{
            background: '#fff',
            padding: 0,
            fontWeight: 600,
            fontSize: 20,
            color: '#1e3c72',
            boxShadow: '0 1px 4px rgba(0,0,0,0.03)'
          }}>
            库存管理系统
          </Header>
          <Content style={{ padding: 24, minHeight: 'calc(100vh - 64px)', height: '100%', width: '100%' }}>
            {/* 内容区100%自适应宽度，背景色填满，无空白 */}
            {children}
          </Content>
        </Layout>
      </div>
    </div>
  );
};

export default MainLayout; 