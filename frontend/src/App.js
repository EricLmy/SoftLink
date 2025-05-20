import React, { useState, useEffect, useCallback } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useNavigate,
  Navigate, // Import Navigate for conditional routing
  useLocation
} from "react-router-dom";
import { Layout, Menu, Typography, Space, Button, message, Spin, Result, Row, Tag, Avatar, Dropdown, Breadcrumb } from 'antd';
import { 
  HomeOutlined, UserOutlined, AppstoreOutlined, SettingOutlined, LogoutOutlined,
  QuestionCircleOutlined,
  TeamOutlined, // Icon for SubAccounts
  SolutionOutlined, // Icon for Admin Users
  AppstoreAddOutlined, // Icon for Admin Features
  MenuUnfoldOutlined, // Added for AdminMenuPage
  MessageOutlined, // Added for AdminFeedbackPage
  EditOutlined, // Added for FeedbackPage
  CrownOutlined // Added for VIPSubscriptionPage
} from '@ant-design/icons';
import './App.css'; 
import LoginPage from './pages/LoginPage';
import FeedbackPage from './pages/FeedbackPage';
import UserProfilePage from './pages/UserProfilePage'; // Import UserProfilePage
import SubAccountsPage from './pages/SubAccountsPage'; // Import SubAccountsPage
import AdminUsersPage from './pages/AdminUsersPage'; // Import AdminUsersPage
import AdminFeaturesPage from './pages/AdminFeaturesPage'; // Import AdminFeaturesPage
import AdminMenuPage from './pages/AdminMenuPage'; // Import AdminMenuPage
import AdminFeedbackPage from './pages/AdminFeedbackPage'; // Import AdminFeedbackPage
import VIPSubscriptionPage from './pages/VIPSubscriptionPage'; // Import VIPSubscriptionPage
import SettingsPage from './pages/SettingsPage'; // Import SettingsPage
import AppCenterPage from './pages/AppCenterPage'; // 导入应用中心页面
import { authService, userService, featureService } from './services/api';
import './i18n';
import { useTranslation } from 'react-i18next';

const { Header, Content, Footer, Sider } = Layout;
const { Title, Text } = Typography;

// 页面标题映射
const pageTitleMap = {
  '/': '首页',
  '/profile': '个人中心',
  '/settings': '系统设置',
  '/feedback': '意见反馈',
  '/sub-accounts': '子账户管理',
  '/vip': 'VIP会员订阅',
  '/app-center': '应用中心', // 添加应用中心页面标题
  '/admin/users': '用户管理',
  '/admin/features': '功能模块配置',
  '/admin/menu': '动态菜单配置',
  '/admin/feedback': '用户反馈查阅'
};

// Placeholder components for routes
const HomePage = () => <Title level={2}>首页</Title>;
// const UserManagementPage = () => <Title level={2}>用户管理 (父账户)</Title>; // More specific based on roles
// const AdminUsersPage = () => <Title level={2}>用户列表 (管理员)</Title>;
// const FeatureMarketPage = () => <Title level={2}>功能市场/应用中心</Title>; // This will be dynamic
const NotFoundPage = () => <Result status="404" title="404" subTitle="抱歉，您访问的页面不存在。" extra={<Link to="/"><Button type="primary">返回首页</Button></Link>} />;

// Helper to create menu items from backend data
const IconMap = {
  HomeOutlined,
  UserOutlined,
  AppstoreOutlined,
  SettingOutlined,
  LogoutOutlined,
  QuestionCircleOutlined,
  TeamOutlined,
  SolutionOutlined,
  AppstoreAddOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  EditOutlined,
  // Add more Ant Design icons here as needed and ensure they are imported
  // e.g. DashboardOutlined, ClusterOutlined, ShoppingCartOutlined etc.
};

const createMenuItems = (menuData) => {
  if (!menuData || !Array.isArray(menuData)) return [];
  
  return menuData.map(item => {
    // 确保item是有效对象
    if (!item) return null;
    
    let iconToRender = <AppstoreOutlined />; // Default icon
    if (item.icon && IconMap[item.icon]) {
      const IconComponent = IconMap[item.icon];
      iconToRender = <IconComponent />;
    } else if (item.icon) {
      // Fallback for icons not in IconMap or if a generic string was provided
      if (item.icon.toLowerCase().includes('home')) iconToRender = <HomeOutlined />;
      else if (item.icon.toLowerCase().includes('user')) iconToRender = <UserOutlined />;
      else if (item.icon.toLowerCase().includes('setting')) iconToRender = <SettingOutlined />;
      else if (item.icon.toLowerCase().includes('appstore')) iconToRender = <AppstoreAddOutlined />;
      console.warn(`Icon string "${item.icon}" not found in IconMap, using fallback or default.`);
    }

    // 处理子菜单
    if (item.children && item.children.length > 0) {
      const children = createMenuItems(item.children).filter(Boolean); // 过滤掉null项
      if (children.length === 0) {
        // 如果没有有效子菜单，则返回普通菜单项
        return renderMenuItem(item, iconToRender);
      }
      
      return (
        <Menu.SubMenu 
          key={item.url || `submenu-${item.id || Math.random().toString(36).substr(2, 9)}`} 
          icon={iconToRender} 
          title={item.name || '未命名菜单'}
        >
          {children}
        </Menu.SubMenu>
      );
    }
    
    return renderMenuItem(item, iconToRender);
  }).filter(Boolean); // 过滤掉null项
};

// 抽取渲染单个菜单项的函数
const renderMenuItem = (item, icon) => {
  // 验证URL
  const isExternalLink = item.url && item.url.startsWith('http');
  const url = item.url || '/';
  
  // 确保有key值
  const menuKey = item.url || `menu-${item.id || Math.random().toString(36).substr(2, 9)}`;
  
  return (
    <Menu.Item key={menuKey} icon={icon}>
      {isExternalLink ? (
        <a href={url} target="_blank" rel="noopener noreferrer">
          {item.name || '未命名菜单'}
        </a>
      ) : (
        <Link to={url}>
          {item.name || '未命名菜单'}
        </Link>
      )}
    </Menu.Item>
  );
};

// 为动态菜单项构建标题映射
const buildDynamicTitleMap = (menuItems) => {
  const titleMap = {};
  
  if (!menuItems || !Array.isArray(menuItems)) {
    return titleMap;
  }
  
  const processList = (items) => {
    if (!items || !Array.isArray(items)) return;
    
    items.forEach(item => {
      if (!item) return;
      
      if (item.url && typeof item.url === 'string' && item.name) {
        titleMap[item.url] = item.name;
      }
      
      if (item.children && Array.isArray(item.children) && item.children.length > 0) {
        processList(item.children);
      }
    });
  };
  
  processList(menuItems);
  return titleMap;
};

// 路径面包屑组件
const PathBreadcrumb = ({ path, titleMap, t }) => {
  // 移除末尾的斜杠
  const cleanPath = path.endsWith('/') ? path.slice(0, -1) : path;
  
  // 根目录特殊处理
  if (cleanPath === '') {
    return (
      <Breadcrumb>
        <Breadcrumb.Item>首页</Breadcrumb.Item>
      </Breadcrumb>
    );
  }
  
  // 分割路径
  const pathSegments = cleanPath.split('/').filter(segment => segment !== '');
  
  // 构建面包屑项
  const breadcrumbItems = [];
  let currentPath = '';
  
  // 首页始终作为第一项
  breadcrumbItems.push(
    <Breadcrumb.Item key="home">
      <Link to="/">{t('首页')}</Link>
    </Breadcrumb.Item>
  );
  
  // 添加其他路径段
  pathSegments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const isLast = index === pathSegments.length - 1;
    
    // 查找当前路径对应的标题
    let title = titleMap[currentPath] || segment;
    
    // 管理员路径特殊处理
    if (segment === 'admin' && index === 0) {
      title = '系统管理';
    }
    
    breadcrumbItems.push(
      <Breadcrumb.Item key={currentPath}>
        {isLast ? (
          <span>{title}</span>
        ) : (
          <Link to={currentPath}>{title}</Link>
        )}
      </Breadcrumb.Item>
    );
  });
  
  return <Breadcrumb>{breadcrumbItems}</Breadcrumb>;
};

function AppContent() {
  const { t } = useTranslation();
  const [currentUser, setCurrentUser] = useState(null);
  const [dynamicMenu, setDynamicMenu] = useState([]);
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState(false);
  const [error, setError] = useState(null);
  const [selectedKeys, setSelectedKeys] = useState(['/']);
  const [dynamicTitleMap, setDynamicTitleMap] = useState({});
  const location = useLocation();

  // 合并静态和动态标题映射
  const titleMap = { ...pageTitleMap, ...dynamicTitleMap };
  
  // 当路径变化时更新选中的菜单项
  useEffect(() => {
    const path = location.pathname;
    setSelectedKeys([path]);
  }, [location.pathname]);

  // 完全重写这个函数，移除所有不必要的依赖
  const fetchInitialData = useCallback(async () => {
    // 设置加载状态
    setLoading(true);
    
    // 检查是否已登录
    const token = localStorage.getItem('accessToken');
    if (!token) {
      setLoading(false);
      return; // 如果没有token，直接返回，不要请求API
    }
    
    try {
      // 获取用户信息
      const userProfileResponse = await userService.getProfile();
      if (userProfileResponse?.data) {
        setCurrentUser(userProfileResponse.data);
        
        // 仅在用户信息成功获取后请求菜单
        try {
          const menuResponse = await featureService.getDynamicMenu();
          const menuData = menuResponse.data || [];
          
          // 一次性设置所有状态，避免多次渲染
          setDynamicMenu(menuData);
          setDynamicTitleMap(buildDynamicTitleMap(menuData));
        } catch (menuErr) {
          console.error("获取动态菜单失败:", menuErr);
          setDynamicMenu([]);
          setError("无法加载动态菜单项，部分导航功能可能受限。");
        }
      }
    } catch (err) {
      console.error("获取用户信息失败:", err);
      // 清除无效token
      localStorage.removeItem('accessToken');
      setCurrentUser(null);
      setDynamicMenu([]);
      setError("无法加载用户信息，请重新登录。");
    } finally {
      // 无论成功失败都关闭加载状态
      setLoading(false);
    }
  }, []); // 移除所有依赖，确保只在组件挂载时执行一次

  // 只在组件挂载时执行一次获取数据
  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const handleLoginSuccess = (token, userInfo) => {
    localStorage.setItem('accessToken', token);
    // 直接设置用户信息，避免多余的API请求
    setCurrentUser(userInfo);
    // 登录成功后获取菜单数据
    fetchInitialData();
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    setCurrentUser(null);
    setDynamicMenu([]);
    message.success('已成功登出。');
  };

  const handleMenuSelect = ({ key }) => {
    setSelectedKeys([key]);
  };

  if (loading) {
    return <Row justify="center" align="middle" style={{minHeight: '100vh'}}><Spin size="large" tip="加载中..." /></Row>;
  }

  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }
  
  if (error) {
      return <Result status="warning" title="加载失败" subTitle={error} extra={<Button type="primary" onClick={() => {setError(null); setLoading(true); fetchInitialData();}}>重试</Button>} />
  }

  const menuItemsFromBackend = createMenuItems(dynamicMenu);
  
  // 获取当前页面标题
  const currentPath = location.pathname;
  const currentTitle = titleMap[currentPath] || '未知页面';

  return (
      <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          className="custom-sider"
          breakpoint="lg"
          collapsedWidth={80} // 折叠后显示图标，而不是完全消失
        >
          <div className="logo">
            {collapsed ? t('牧联') : t('牧联 SoftLink')}
          </div>
          <Menu 
            theme="dark" 
            selectedKeys={selectedKeys}
            defaultOpenKeys={['admin-menu']} 
            mode="inline"
            onSelect={handleMenuSelect}
          >
            <Menu.Item key="/" icon={<HomeOutlined />}>
              <Link to="/">{t('首页')}</Link>
            </Menu.Item>
            <Menu.Item key="/profile" icon={<UserOutlined />}>
              <Link to="/profile">{t('个人中心')}</Link>
            </Menu.Item>
            <Menu.Item key="/settings" icon={<SettingOutlined />}>
              <Link to="/settings">{t('系统设置')}</Link>
            </Menu.Item>
            <Menu.Item key="/app-center" icon={<AppstoreOutlined />}>
              <Link to="/app-center">{t('应用中心')}</Link>
            </Menu.Item>
            {menuItemsFromBackend} 
            {/* Static Menu Items based on roles can also be added here or merged with dynamic ones */}
            {currentUser.role === 'parent_user' && (
                <Menu.Item key="/sub-accounts" icon={<TeamOutlined />}>
                    <Link to="/sub-accounts">{t('子账户管理')}</Link>
                </Menu.Item>
            )}
            {currentUser.role === 'super_admin' && (
                <Menu.SubMenu key="admin-menu" icon={<SettingOutlined />} title={t('系统管理')}>
                    <Menu.Item key="/admin/users" icon={<SolutionOutlined />}>
                        <Link to="/admin/users">{t('用户管理')}</Link>
                    </Menu.Item>
                    <Menu.Item key="/admin/features" icon={<AppstoreAddOutlined />}>
                        <Link to="/admin/features">{t('功能模块配置')}</Link>
                    </Menu.Item>
                    <Menu.Item key="/admin/menu" icon={<MenuUnfoldOutlined />}>
                        <Link to="/admin/menu">{t('动态菜单配置')}</Link>
                    </Menu.Item>
                    <Menu.Item key="/admin/feedback" icon={<MessageOutlined />}>
                        <Link to="/admin/feedback">{t('用户反馈查阅')}</Link>
                    </Menu.Item>
                </Menu.SubMenu>
            )}
             <Menu.Item key="/feedback" icon={<EditOutlined />}>
              <Link to="/feedback">{t('意见反馈')}</Link>
            </Menu.Item>
            <Menu.Item key="/vip" icon={<CrownOutlined />}>
              <Link to="/vip">{t('VIP会员订阅')}</Link>
            </Menu.Item>
            <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={handleLogout}>
              {t('登出')}
            </Menu.Item>
          </Menu>
        </Sider>
        <Layout className="site-layout">
          <Header className="site-layout-background" style={{ 
            padding: '0 16px', 
            background: '#fff',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.09)',
            position: 'sticky',
            top: 0,
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            {/* 左侧标题区域 - 动态显示当前页面标题 */}
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div className="page-header">
                <Title level={4} style={{ margin: 0, fontSize: '18px' }}>
                  {t(currentTitle)}
                </Title>
                <div className="breadcrumb-container">
                  <PathBreadcrumb path={currentPath} titleMap={titleMap} t={t} />
                </div>
              </div>
            </div>
            
            {/* 右侧用户信息区域 */}
            <Space>
              {currentUser.vip_level_name && (
                <Tag color="gold" style={{ marginRight: '8px' }}>
                  {currentUser.vip_level_name}
                </Tag>
              )}
              <Dropdown 
                overlay={
                  <Menu>
                    <Menu.Item key="profile" icon={<UserOutlined />}>
                      <Link to="/profile">{t('个人中心')}</Link>
                    </Menu.Item>
                    <Menu.Divider />
                    <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={handleLogout}>
                      {t('退出登录')}
                    </Menu.Item>
                  </Menu>
                } 
                placement="bottomRight"
              >
                <Space style={{ cursor: 'pointer' }}>
                  <Avatar 
                    icon={<UserOutlined />} 
                    style={{ backgroundColor: '#1890ff' }}
                  />
                  <span className="hide-on-mobile">
                    {currentUser.username}
                    <Text type="secondary" style={{ marginLeft: 8 }}>
                      {currentUser.role === 'super_admin' ? t('超级管理员') : 
                       currentUser.role === 'parent_user' ? t('父账户') : 
                       currentUser.role === 'sub_account' ? t('子账户') : 
                       currentUser.role}
                    </Text>
                  </span>
                </Space>
              </Dropdown>
            </Space>
          </Header>
          <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
            <div className="site-layout-background custom-card" style={{ padding: 24, minHeight: 360 }}>
              <Routes>
                <Route path="/" element={<Title level={2}>{t('首页')}</Title>} />
                <Route path="/profile" element={<UserProfilePage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/feedback" element={<FeedbackPage />} />
                <Route path="/app-center" element={<AppCenterPage />} />
                {/* Conditional route for SubAccountsPage */}
                {currentUser.role === 'parent_user' ? (
                  <Route path="/sub-accounts" element={<SubAccountsPage />} />
                ) : (
                  <Route path="/sub-accounts" element={<Navigate to="/" replace />} />
                )}
                {/* Conditional routes for Admin pages */}
                {currentUser.role === 'super_admin' ? (
                  <>
                    <Route path="/admin/users" element={<AdminUsersPage />} />
                    <Route path="/admin/features" element={<AdminFeaturesPage />} />
                    <Route path="/admin/menu" element={<AdminMenuPage />} />
                    <Route path="/admin/feedback" element={<AdminFeedbackPage />} />
                  </>
                ) : (
                  <>
                    <Route path="/admin/users" element={<Navigate to="/" replace />} />
                    <Route path="/admin/features" element={<Navigate to="/" replace />} />
                    <Route path="/admin/menu" element={<Navigate to="/" replace />} />
                    <Route path="/admin/feedback" element={<Navigate to="/" replace />} />
                  </>
                )}
                {/* 动态路由 */}
                {dynamicMenu && dynamicMenu.map(item => {
                  // 如果item没有url或url为空，不创建路由
                  if (!item.url || item.url.trim() === '') {
                    return null;
                  }
                  
                  if (item.children && item.children.length > 0) {
                    return item.children
                      .filter(child => child.url && child.url.trim() !== '')
                      .map(child => (
                        <Route 
                          key={`route-${child.id || child.url}`} 
                          path={child.url} 
                          element={<Title level={3}>{t('页面')}: {child.name}</Title>} 
                        />
                      ));
                  }
                  
                  return (
                    <Route 
                      key={`route-${item.id || item.url}`} 
                      path={item.url} 
                      element={<Title level={3}>{t('页面')}: {item.name}</Title>} 
                    />
                  );
                })}
                <Route path="/vip" element={<VIPSubscriptionPage />} />
                <Route path="*" element={<Result status="404" title="404" subTitle={t('抱歉，您访问的页面不存在。')} extra={<Link to="/"><Button type="primary">{t('返回首页')}</Button></Link>} />} />
              </Routes>
            </div>
          </Content>
          <Footer style={{ 
            textAlign: 'center',
            background: '#f0f2f5',
            padding: '12px 24px',
            color: 'rgba(0, 0, 0, 0.45)'
          }}>
            牧联 (SoftLink) ©{new Date().getFullYear()} Created by SoftLink Team
          </Footer>
        </Layout>
      </Layout>
  );
}

function App() {
  // 在应用加载时应用保存的主题和语言设置
  useEffect(() => {
    // 从localStorage获取保存的主题
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      // 移除所有主题相关的类名
      document.body.classList.remove('theme-light', 'theme-dark', 'theme-科技蓝');
      // 添加保存的主题类名
      document.body.classList.add(`theme-${savedTheme}`);
      console.log(`已从本地存储加载主题: ${savedTheme}`);
    } else {
      // 默认使用浅色主题
      document.body.classList.add('theme-light');
    }
    
    // 从localStorage获取保存的语言设置
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage) {
      console.log(`已从本地存储加载语言设置: ${savedLanguage}`);
      // 这里可以触发应用的语言切换
      // 如果使用i18n框架，可以在这里调用其API
    }
  }, []);

  return (
    <AppContent />
  );
}

export default App; 