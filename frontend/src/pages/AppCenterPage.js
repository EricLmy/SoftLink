import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Button, 
  Tag, 
  Spin, 
  Alert, 
  Modal, 
  message,
  Tooltip,
  Empty,
  Divider
} from 'antd';
import { 
  AppstoreOutlined, 
  ExperimentOutlined, 
  LockOutlined, 
  CheckCircleOutlined,
  ClockCircleOutlined,
  CrownOutlined
} from '@ant-design/icons';
import { featureService } from '../services/api';

const { Title, Text, Paragraph } = Typography;

const AppCenterPage = () => {
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState(null);
  
  useEffect(() => {
    fetchFeatures();
  }, []);

  const fetchFeatures = async () => {
    try {
      setLoading(true);
      const response = await featureService.getFeatures();
      setFeatures(response.data);
      setError(null);
    } catch (err) {
      console.error('获取功能列表失败:', err);
      setError('获取功能列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const startTrial = async (featureIdentifier) => {
    try {
      const response = await featureService.startTrial(featureIdentifier);
      message.success('功能试用已开始！');
      fetchFeatures(); // 刷新功能列表
      setModalVisible(false);
    } catch (err) {
      console.error('开始试用失败:', err);
      message.error(err.response?.data?.message || '开始试用失败，请稍后重试');
    }
  };

  const openFeatureModal = (feature) => {
    setSelectedFeature(feature);
    setModalVisible(true);
  };

  const renderAccessStatus = (feature) => {
    switch (feature.user_access_status) {
      case 'full_access':
        return <Tag color="green" icon={<CheckCircleOutlined />}>完全访问</Tag>;
      case 'trial_active':
        return (
          <Tooltip title={`试用截止日期: ${new Date(feature.trial_end_at).toLocaleDateString()}`}>
            <Tag color="blue" icon={<ExperimentOutlined />}>试用中</Tag>
          </Tooltip>
        );
      case 'trial_available':
        return <Tag color="gold" icon={<ClockCircleOutlined />}>可试用</Tag>;
      case 'trial_expired':
        return <Tag color="volcano" icon={<ClockCircleOutlined />}>试用已过期</Tag>;
      case 'vip_required':
        return <Tag color="magenta" icon={<CrownOutlined />}>需要VIP</Tag>;
      case 'restricted':
      default:
        return <Tag color="red" icon={<LockOutlined />}>受限制</Tag>;
    }
  };

  const renderActionButton = (feature) => {
    switch (feature.user_access_status) {
      case 'full_access':
        return (
          <Button type="primary" href={`#/feature/${feature.identifier}`}>
            立即使用
          </Button>
        );
      case 'trial_active':
        return (
          <Button type="primary" href={`#/feature/${feature.identifier}`}>
            继续使用
          </Button>
        );
      case 'trial_available':
        return (
          <Button type="primary" ghost onClick={() => openFeatureModal(feature)}>
            开始试用
          </Button>
        );
      case 'trial_expired':
      case 'vip_required':
        return (
          <Button type="primary" danger href="#/vip-subscription">
            升级VIP
          </Button>
        );
      case 'restricted':
      default:
        return (
          <Button disabled>
            不可用
          </Button>
        );
    }
  };

  const renderFeatureModal = () => {
    if (!selectedFeature) return null;

    return (
      <Modal
        title={`开始试用 - ${selectedFeature.name}`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            取消
          </Button>,
          <Button 
            key="trial" 
            type="primary" 
            onClick={() => startTrial(selectedFeature.identifier)}
          >
            开始{selectedFeature.trial_days}天免费试用
          </Button>,
        ]}
      >
        <Paragraph>{selectedFeature.description}</Paragraph>
        <Divider />
        <Paragraph>
          <Text strong>试用天数:</Text> {selectedFeature.trial_days}天
        </Paragraph>
        <Paragraph>
          <Text strong>试用结束后:</Text> 需要{' '}
          {selectedFeature.min_vip_level_required ? (
            <Tag color="gold">{selectedFeature.min_vip_level_required.name}</Tag>
          ) : (
            <Tag color="gold">VIP会员</Tag>
          )}{' '}
          才能继续使用
        </Paragraph>
      </Modal>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="获取数据失败"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <Title level={2}><AppstoreOutlined /> 应用中心</Title>
        <Paragraph>
          探索所有可用的功能和应用，开始免费试用或升级到VIP以解锁更多功能。
        </Paragraph>
      </div>

      {features.length === 0 ? (
        <Empty description="暂无可用功能" />
      ) : (
        <Row gutter={[16, 16]}>
          {features.map(feature => (
            <Col xs={24} sm={12} md={8} lg={6} key={feature.id}>
              <Card
                hoverable
                cover={
                  <div style={{ 
                    height: 120, 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    background: '#f5f5f5'
                  }}>
                    {feature.icon ? (
                      <img 
                        alt={feature.name} 
                        src={feature.icon} 
                        style={{ maxHeight: '80%', maxWidth: '80%' }}
                      />
                    ) : (
                      <AppstoreOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                    )}
                  </div>
                }
                actions={[renderActionButton(feature)]}
              >
                <Card.Meta
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>{feature.name}</span>
                      {renderAccessStatus(feature)}
                    </div>
                  }
                  description={
                    <Paragraph ellipsis={{ rows: 3 }}>
                      {feature.description || '暂无描述'}
                    </Paragraph>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {renderFeatureModal()}
    </div>
  );
};

export default AppCenterPage; 