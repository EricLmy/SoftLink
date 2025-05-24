import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, message } from 'antd';
import { request } from '../utils/request';
import { formatDateTime } from '../utils/format';

interface Alert {
  id: number;
  product_id: number;
  product_name: string;
  type: string;
  content: string;
  status: string;
  created_at: string;
}

const Alert: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await request.get('/alert');
      setAlerts(response.data.data);
    } catch (error) {
      message.error('获取告警列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAlert = async (id: number) => {
    try {
      await request.post(`/alert/${id}/handle`);
      message.success('处理成功');
      fetchAlerts();
    } catch (error) {
      message.error('处理失败');
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const columns = [
    {
      title: '商品',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const color = type === 'inventory_low' ? 'red' : 'orange';
        const text = type === 'inventory_low' ? '库存不足' : '库存预警';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'pending' ? 'red' : 'green';
        const text = status === 'pending' ? '待处理' : '已处理';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => formatDateTime(time),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Alert) => (
        record.status === 'pending' && (
          <Button type="link" onClick={() => handleAlert(record.id)}>
            标记为已处理
          </Button>
        )
      ),
    },
  ];

  return (
    <Card title="告警中心">
      <Table
        columns={columns}
        dataSource={alerts}
        rowKey="id"
        loading={loading}
      />
    </Card>
  );
};

export default Alert; 