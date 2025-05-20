import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Typography, Button, Spin, Alert, Badge, 
  message, Tabs, List, Divider, Modal, Radio, Space, Tag
} from 'antd';
import { 
  CrownOutlined, CheckCircleOutlined, CloseCircleOutlined, 
  InfoCircleOutlined, DollarOutlined, UserOutlined
} from '@ant-design/icons';
import { vipService } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// 会员等级特权功能列表示例
const vipFeatures = [
  { key: 'subAccounts', name: '子账户数量', values: { 'VIP1': '10个', 'VIP2': '20个', 'VIP3': '50个', 'VIP4': '无限' } },
  { key: 'features', name: '高级功能', values: { 'VIP1': '✓', 'VIP2': '✓', 'VIP3': '✓', 'VIP4': '✓' } },
  { key: 'storage', name: '存储空间', values: { 'VIP1': '5GB', 'VIP2': '20GB', 'VIP3': '100GB', 'VIP4': '不限' } },
  { key: 'priority', name: '优先客服', values: { 'VIP1': '×', 'VIP2': '✓', 'VIP3': '✓', 'VIP4': '✓' } },
  { key: 'api', name: 'API访问', values: { 'VIP1': '基础', 'VIP2': '标准', 'VIP3': '高级', 'VIP4': '完整' } },
  { key: 'customization', name: '定制功能', values: { 'VIP1': '×', 'VIP2': '×', 'VIP3': '有限', 'VIP4': '完整' } },
];

const VIPSubscriptionPage = () => {
  const [vipLevels, setVipLevels] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [subscribing, setSubscribing] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [paymentType, setPaymentType] = useState('monthly');
  const [modalVisible, setModalVisible] = useState(false);

  // 加载VIP等级信息
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // 获取VIP等级
        const vipResponse = await vipService.getVipLevels();
        setVipLevels(vipResponse.data);
        
        // 获取当前订阅信息
        try {
          const subscriptionResponse = await vipService.getCurrentSubscription();
          setCurrentSubscription(subscriptionResponse.data);
        } catch (subError) {
          console.error('获取当前订阅信息失败:', subError);
          // 不阻止页面加载，用户可能没有订阅
        }
        
        setError(null);
      } catch (err) {
        console.error('加载VIP信息失败:', err);
        setError('加载VIP信息时出错，请稍后再试');
        
        // 开发模式下使用模拟数据
        if (process.env.NODE_ENV === 'development') {
          const mockVipLevels = [
            { 
              id: 1, 
              name: 'VIP1', 
              sub_account_limit: 10,
              monthly_price: 99,
              quarterly_price: 279,
              annual_price: 999,
              lifetime_price: null,
              description: 'VIP1基础会员，适合小型团队'
            },
            { 
              id: 2, 
              name: 'VIP2', 
              sub_account_limit: 20,
              monthly_price: 199,
              quarterly_price: 549,
              annual_price: 1999,
              lifetime_price: null,
              description: 'VIP2高级会员，更多子账户和功能'
            },
            { 
              id: 3, 
              name: 'VIP3', 
              sub_account_limit: 50,
              monthly_price: 399,
              quarterly_price: 1099,
              annual_price: 3999,
              lifetime_price: null,
              description: 'VIP3专业会员，企业级功能与支持'
            },
            { 
              id: 4, 
              name: 'VIP4', 
              sub_account_limit: -1, // -1表示无限
              monthly_price: null,
              quarterly_price: null,
              annual_price: null,
              lifetime_price: 9999,
              description: 'VIP4终身会员，一次付费永久使用'
            }
          ];
          setVipLevels(mockVipLevels);
          
          // 模拟用户没有订阅
          setCurrentSubscription({
            has_subscription: false,
            message: "当前没有有效的VIP订阅"
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // 处理订阅按钮点击
  const handleSubscribeClick = (vipLevel) => {
    setSelectedLevel(vipLevel);
    
    // 根据VIP等级设置默认支付类型
    if (vipLevel.name === 'VIP4') {
      setPaymentType('lifetime');
    } else {
      setPaymentType('monthly'); // 默认月付
    }
    
    setModalVisible(true);
  };

  // 处理订阅确认
  const handleSubscribeConfirm = async () => {
    if (!selectedLevel || !paymentType) {
      message.error('请选择会员等级和支付方式');
      return;
    }
    
    // 验证价格有效性
    let price = null;
    if (paymentType === 'monthly') price = selectedLevel.monthly_price;
    else if (paymentType === 'quarterly') price = selectedLevel.quarterly_price;
    else if (paymentType === 'annual') price = selectedLevel.annual_price;
    else if (paymentType === 'lifetime') price = selectedLevel.lifetime_price;
    
    if (price === null) {
      message.error(`${selectedLevel.name} 不支持 ${paymentType} 支付方式`);
      return;
    }
    
    try {
      setSubscribing(true);
      const response = await vipService.subscribeVip({
        vip_level_id: selectedLevel.id,
        payment_type: paymentType
      });
      
      message.success(response.data.message || '订阅成功！');
      setModalVisible(false);
      
      // 刷新订阅信息
      const subscriptionResponse = await vipService.getCurrentSubscription();
      setCurrentSubscription(subscriptionResponse.data);
    } catch (err) {
      console.error('订阅失败:', err);
      message.error(err.response?.data?.message || '订阅处理失败，请稍后再试');
    } finally {
      setSubscribing(false);
    }
  };

  // 处理支付类型变更
  const handlePaymentTypeChange = (e) => {
    setPaymentType(e.target.value);
  };

  // 获取支付类型描述
  const getPaymentTypeLabel = (type) => {
    switch (type) {
      case 'monthly': return '月付';
      case 'quarterly': return '季付';
      case 'annual': return '年付';
      case 'lifetime': return '终身';
      default: return type;
    }
  };

  // 获取价格显示
  const getPriceDisplay = (vipLevel, type) => {
    let price = null;
    
    if (type === 'monthly') price = vipLevel.monthly_price;
    else if (type === 'quarterly') price = vipLevel.quarterly_price;
    else if (type === 'annual') price = vipLevel.annual_price;
    else if (type === 'lifetime') price = vipLevel.lifetime_price;
    
    if (price === null) return '不支持';
    return `¥${price}`;
  };

  // 渲染当前订阅信息
  const renderCurrentSubscription = () => {
    if (!currentSubscription) return null;
    
    if (!currentSubscription.has_subscription) {
      return (
        <Alert
          message="您当前没有VIP订阅"
          description="订阅VIP可享受更多功能和服务，解锁更多可能性！"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      );
    }
    
    const { subscription, vip_level, expiry_date, days_remaining } = currentSubscription;
    
    return (
      <Card 
        title={<><CrownOutlined /> 当前订阅信息</>} 
        style={{ marginBottom: 24 }}
        className="vip-subscription-card"
      >
        <Row gutter={16}>
          <Col span={8}>
            <Text strong>会员等级:</Text>
          </Col>
          <Col span={16}>
            <Badge status="processing" text={vip_level} style={{ fontWeight: 'bold' }} />
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 12 }}>
          <Col span={8}>
            <Text strong>到期时间:</Text>
          </Col>
          <Col span={16}>
            <Text>{new Date(expiry_date).toLocaleDateString('zh-CN')}</Text>
            <Tag color="blue" style={{ marginLeft: 8 }}>
              剩余 {days_remaining} 天
            </Tag>
          </Col>
        </Row>
        {subscription.payment_type && (
          <Row gutter={16} style={{ marginTop: 12 }}>
            <Col span={8}>
              <Text strong>付款方式:</Text>
            </Col>
            <Col span={16}>
              <Text>{getPaymentTypeLabel(subscription.payment_type)}</Text>
            </Col>
          </Row>
        )}
      </Card>
    );
  };

  // 条件渲染 - 加载中
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载中...</div>
      </div>
    );
  }

  // 条件渲染 - 错误
  if (error && !vipLevels.length) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div className="vip-subscription-page">
      <Title level={2}>
        <CrownOutlined style={{ marginRight: 8 }} />
        VIP会员订阅
      </Title>
      
      {/* 当前订阅信息 */}
      {renderCurrentSubscription()}
      
      {/* 会员对比表格 */}
      <Tabs defaultActiveKey="cards" style={{ marginTop: 24 }}>
        <TabPane tab="会员对比" key="cards">
          <Row gutter={16}>
            {vipLevels.map(level => (
              <Col xs={24} sm={12} md={6} key={level.id}>
                <Card
                  title={
                    <div style={{ textAlign: 'center' }}>
                      <CrownOutlined style={{ color: '#faad14', marginRight: 8 }} />
                      <Text strong>{level.name}</Text>
                    </div>
                  }
                  className="vip-card"
                  style={{ 
                    marginBottom: 16, 
                    height: '100%',
                    border: level.name === 'VIP4' ? '2px solid #1890ff' : undefined
                  }}
                >
                  {level.name === 'VIP4' && (
                    <Badge.Ribbon text="推荐" color="blue" />
                  )}
                  
                  <div style={{ textAlign: 'center', marginBottom: 16 }}>
                    <Paragraph>{level.description}</Paragraph>
                    
                    {/* 子账户数量 */}
                    <div style={{ margin: '12px 0' }}>
                      <UserOutlined /> 子账户: {level.sub_account_limit === -1 ? '无限' : level.sub_account_limit}个
                    </div>
                    
                    {/* 价格展示 */}
                    <div className="price-container" style={{ margin: '24px 0' }}>
                      {level.monthly_price && (
                        <div>
                          <Text type="secondary">月付</Text>
                          <div>
                            <Text style={{ fontSize: 24, fontWeight: 'bold' }}>¥{level.monthly_price}</Text>
                          </div>
                        </div>
                      )}
                      
                      {level.annual_price && (
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">年付</Text>
                          <div>
                            <Text style={{ fontSize: 18, fontWeight: 'bold' }}>¥{level.annual_price}</Text>
                            <Tag color="green" style={{ marginLeft: 8 }}>优惠</Tag>
                          </div>
                        </div>
                      )}
                      
                      {level.lifetime_price && (
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">终身会员</Text>
                          <div>
                            <Text style={{ fontSize: 24, fontWeight: 'bold' }}>¥{level.lifetime_price}</Text>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <Button 
                      type="primary" 
                      size="large"
                      block
                      onClick={() => handleSubscribeClick(level)}
                    >
                      立即订阅
                    </Button>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>
        
        <TabPane tab="功能详情" key="features">
          <Card>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ padding: 16, borderBottom: '1px solid #f0f0f0', textAlign: 'left' }}>功能</th>
                    {vipLevels.map(level => (
                      <th 
                        key={level.id} 
                        style={{ 
                          padding: 16, 
                          borderBottom: '1px solid #f0f0f0',
                          textAlign: 'center',
                          backgroundColor: level.name === 'VIP4' ? '#f0f8ff' : undefined
                        }}
                      >
                        {level.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {vipFeatures.map(feature => (
                    <tr key={feature.key}>
                      <td style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
                        {feature.name}
                      </td>
                      {vipLevels.map(level => (
                        <td 
                          key={`${feature.key}-${level.id}`} 
                          style={{ 
                            padding: 16, 
                            borderBottom: '1px solid #f0f0f0',
                            textAlign: 'center',
                            backgroundColor: level.name === 'VIP4' ? '#f0f8ff' : undefined
                          }}
                        >
                          {feature.values[level.name] || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </TabPane>
      </Tabs>
      
      {/* 订阅确认对话框 */}
      <Modal
        title={<><CrownOutlined style={{ color: '#faad14' }} /> 确认订阅</>}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="back" onClick={() => setModalVisible(false)}>
            取消
          </Button>,
          <Button 
            key="submit" 
            type="primary" 
            loading={subscribing}
            onClick={handleSubscribeConfirm}
          >
            确认支付
          </Button>,
        ]}
      >
        {selectedLevel && (
          <>
            <div style={{ marginBottom: 16 }}>
              <Text strong>会员等级:</Text> {selectedLevel.name}
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>会员描述:</Text> {selectedLevel.description}
            </div>
            
            <Divider />
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>支付方式:</Text>
              <div style={{ marginTop: 8 }}>
                <Radio.Group onChange={handlePaymentTypeChange} value={paymentType}>
                  <Space direction="vertical">
                    {selectedLevel.monthly_price !== null && (
                      <Radio value="monthly">
                        月付 {getPriceDisplay(selectedLevel, 'monthly')}
                      </Radio>
                    )}
                    {selectedLevel.quarterly_price !== null && (
                      <Radio value="quarterly">
                        季付 {getPriceDisplay(selectedLevel, 'quarterly')}
                        <Tag color="green" style={{ marginLeft: 8 }}>优惠</Tag>
                      </Radio>
                    )}
                    {selectedLevel.annual_price !== null && (
                      <Radio value="annual">
                        年付 {getPriceDisplay(selectedLevel, 'annual')}
                        <Tag color="green" style={{ marginLeft: 8 }}>优惠</Tag>
                      </Radio>
                    )}
                    {selectedLevel.lifetime_price !== null && (
                      <Radio value="lifetime">
                        终身会员 {getPriceDisplay(selectedLevel, 'lifetime')}
                        <Tag color="green" style={{ marginLeft: 8 }}>一次付费，终身使用</Tag>
                      </Radio>
                    )}
                  </Space>
                </Radio.Group>
              </div>
            </div>
            
            <Divider />
            
            <Alert
              message={<><InfoCircleOutlined /> 支付说明</>}
              description="本系统目前为演示阶段，点击确认后将直接模拟支付成功，不会产生实际扣款。"
              type="info"
              showIcon={false}
            />
          </>
        )}
      </Modal>
    </div>
  );
};

export default VIPSubscriptionPage; 