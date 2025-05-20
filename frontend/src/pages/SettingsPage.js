import React, { useState, useEffect } from 'react';
import { 
  Card, Form, Select, Switch, Button, message, 
  Typography, Divider, Row, Col, Radio, Spin, Alert
} from 'antd';
import { 
  SettingOutlined, BgColorsOutlined, GlobalOutlined, 
  BellOutlined, SaveOutlined, LoadingOutlined
} from '@ant-design/icons';
import { preferenceService } from '../services/api';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;
const { Option } = Select;

const SettingsPage = () => {
  const { t, i18n } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [preferences, setPreferences] = useState({
    theme: 'light',
    language: 'zh-CN',
    notification_settings: {
      email_updates: true,
      system_alerts: true
    }
  });

  // 获取用户偏好设置
  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        setLoading(true);
        const response = await preferenceService.getUserPreferences();
        const prefs = response.data;
        
        setPreferences(prefs);
        
        // 设置表单初始值
        form.setFieldsValue({
          theme: prefs.theme,
          language: prefs.language,
          emailUpdates: prefs.notification_settings?.email_updates !== false,
          systemAlerts: prefs.notification_settings?.system_alerts !== false
        });
        
        setError(null);
      } catch (err) {
        console.error('获取用户偏好设置失败:', err);
        setError('获取用户偏好设置时出错，请稍后再试');
        
        // 开发环境下使用默认值
        if (process.env.NODE_ENV === 'development') {
          const defaultPrefs = {
            theme: 'light',
            language: 'zh-CN',
            notification_settings: {
              email_updates: true,
              system_alerts: true
            }
          };
          
          form.setFieldsValue({
            theme: defaultPrefs.theme,
            language: defaultPrefs.language,
            emailUpdates: defaultPrefs.notification_settings.email_updates,
            systemAlerts: defaultPrefs.notification_settings.system_alerts
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, [form]);

  // 处理表单提交
  const handleSubmit = async (values) => {
    try {
      setSaving(true);
      
      // 构造API请求数据结构
      const updateData = {
        theme: values.theme,
        language: values.language,
        notification_settings: {
          email_updates: values.emailUpdates,
          system_alerts: values.systemAlerts
        }
      };
      
      // 调用API更新用户偏好设置
      const response = await preferenceService.updateUserPreferences(updateData);
      
      // 更新本地状态
      setPreferences(response.data.preferences);
      
      message.success('设置已保存');
    } catch (err) {
      console.error('保存用户偏好设置失败:', err);
      message.error(err.response?.data?.message || '保存设置失败，请稍后再试');
    } finally {
      setSaving(false);
    }
  };

  // 应用主题更改
  useEffect(() => {
    if (preferences.theme) {
      // 移除所有主题相关的类名
      document.body.classList.remove('theme-light', 'theme-dark', 'theme-科技蓝');
      // 添加新的主题类名
      document.body.classList.add(`theme-${preferences.theme}`);
      
      // 保存到本地存储，以便页面刷新后保持主题
      localStorage.setItem('theme', preferences.theme);
      
      console.log(`主题已切换为: ${preferences.theme}`);
    }
  }, [preferences.theme]);

  // 应用语言设置
  useEffect(() => {
    if (preferences.language) {
      // 设置语言到本地存储
      localStorage.setItem('language', preferences.language);
      console.log(`语言已设置为: ${preferences.language}`);
      
      // 这里可以触发应用的语言切换
      // 如果使用i18n框架，可以在这里调用其API
    }
  }, [preferences.language]);

  // 语言切换时，动态切换i18n语言
  useEffect(() => {
    if (preferences.language) {
      i18n.changeLanguage(preferences.language);
    }
  }, [preferences.language, i18n]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
        <div style={{ marginTop: 16 }}>{t('正在加载设置...')}</div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <Title level={2}>
        <SettingOutlined /> {t('系统设置')}
      </Title>
      
      {error && (
        <Alert
          message={t('加载错误')}
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            theme: preferences.theme,
            language: preferences.language,
            emailUpdates: preferences.notification_settings?.email_updates,
            systemAlerts: preferences.notification_settings?.system_alerts
          }}
        >
          <Divider orientation="left">
            <BgColorsOutlined /> {t('界面主题')}
          </Divider>
          
          <Form.Item name="theme" label={t('选择主题')}>
            <Radio.Group>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Radio.Button value="light">
                    <div className="theme-preview light-theme">
                      <div className="theme-preview-header"></div>
                      <div className="theme-preview-content"></div>
                    </div>
                    {t('浅色主题')}
                  </Radio.Button>
                </Col>
                <Col span={8}>
                  <Radio.Button value="dark">
                    <div className="theme-preview dark-theme">
                      <div className="theme-preview-header"></div>
                      <div className="theme-preview-content"></div>
                    </div>
                    {t('深色主题')}
                  </Radio.Button>
                </Col>
                <Col span={8}>
                  <Radio.Button value="科技蓝">
                    <div className="theme-preview blue-theme">
                      <div className="theme-preview-header"></div>
                      <div className="theme-preview-content"></div>
                    </div>
                    {t('科技蓝')}
                  </Radio.Button>
                </Col>
              </Row>
            </Radio.Group>
          </Form.Item>
          
          <Divider orientation="left">
            <GlobalOutlined /> {t('语言设置')}
          </Divider>
          
          <Form.Item name="language" label={t('选择语言')}>
            <Select>
              <Option value="zh-CN">{t('简体中文')}</Option>
              <Option value="en-US">{t('English (US)')}</Option>
            </Select>
          </Form.Item>
          
          <Divider orientation="left">
            <BellOutlined /> {t('通知设置')}
          </Divider>
          
          <Form.Item name="emailUpdates" label={t('邮件更新')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Text type="secondary" style={{ display: 'block', marginTop: -15, marginBottom: 16 }}>
            {t('接收产品更新和重要通知邮件')}
          </Text>
          
          <Form.Item name="systemAlerts" label={t('系统提醒')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Text type="secondary" style={{ display: 'block', marginTop: -15, marginBottom: 16 }}>
            {t('在系统中显示重要的提醒和消息')}
          </Text>
          
          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              icon={<SaveOutlined />}
              loading={saving}
            >
              {t('保存设置')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default SettingsPage; 