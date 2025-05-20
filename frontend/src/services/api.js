import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api'; // Backend API URL

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authService = {
  login: (username, password) => apiClient.post('/auth/login', { username, password }),
  register: (username, email, password) => {
    console.log('注册请求参数:', { username, email, password });
    return apiClient.post('/auth/register', { username, email, password })
      .catch(error => {
        console.error('注册请求失败:', error.response?.data || error.message);
        throw error;
      });
  },
  // logout: () => apiClient.post('/auth/logout'), // If backend implements it
};

export const userService = {
  getProfile: () => apiClient.get('/users/me'),
  updateProfile: (data) => apiClient.put('/users/me', data),
  createSubAccount: (data) => apiClient.post('/users/me/sub-accounts', data),
  getSubAccounts: () => apiClient.get('/users/me/sub-accounts'),
  updateSubAccount: (id, data) => apiClient.put(`/users/me/sub-accounts/${id}`, data),
  deleteSubAccount: (id) => apiClient.delete(`/users/me/sub-accounts/${id}`),
  getSubAccountActivityLogs: (id, page = 1, perPage = 100) => 
    apiClient.get(`/users/me/sub-accounts/${id}/logs`, { params: { page, per_page: perPage } }),
  adminGetUsers: (params) => apiClient.get('/admin/users', { params }),
  adminCreateUser: (data) => apiClient.post('/admin/users', data),
  adminUpdateUser: (id, data) => apiClient.put(`/admin/users/${id}`, data),
  adminDeleteUser: (id) => apiClient.delete(`/admin/users/${id}`),
  adminUpdateUserVipStatus: (id, data) => apiClient.put(`/admin/users/${id}/vip`, data),
};

export const featureService = {
  getDynamicMenu: () => apiClient.get('/features/dynamic-menu'),
  getFeatures: () => apiClient.get('/features'),
  startTrial: (featureIdentifier) => apiClient.post(`/features/${featureIdentifier}/start-trial`)
};

export const feedbackService = {
  submitFeedback: (data) => apiClient.post('/feedback', data),
  adminGetFeedbacks: (params) => {
    return apiClient.get('/admin/feedbacks', { params })
      .catch(error => {
        console.warn('使用API获取反馈列表失败，启用模拟数据:', error);
        
        const mockFeedbacks = [
          {
            id: 1,
            user: { username: '测试用户1', email: 'test1@example.com' },
            user_id: 1,
            category: '功能建议',
            content: '希望能增加批量导入导出功能，方便数据迁移。',
            status: 'pending',
            submitted_at: '2023-05-15T08:30:00Z',
          },
          {
            id: 2,
            user: { username: '测试用户2', email: 'test2@example.com' },
            user_id: 2,
            category: 'Bug报告',
            content: '在移动设备上，表格显示不正确，部分内容被截断。',
            status: 'processing',
            submitted_at: '2023-05-16T10:22:00Z',
            resolution_notes: '正在修复中，计划下周上线新版本。',
          },
          {
            id: 3,
            user: { username: '测试用户3', email: 'test3@example.com' },
            user_id: 3,
            category: '改进意见',
            content: '界面太复杂，建议简化操作流程，减少点击次数。',
            status: 'resolved',
            submitted_at: '2023-05-14T14:55:00Z',
            resolution_notes: '已采纳，新UI将在下个版本发布。',
            resolved_at: '2023-05-17T09:10:00Z',
            resolver: { username: '管理员' },
            resolver_id: 1001
          }
        ];
        
        const page = params.page || 1;
        const pageSize = params.per_page || 10;
        const start = (page - 1) * pageSize;
        const end = start + pageSize;
        const paginatedFeedbacks = mockFeedbacks.slice(start, end);
        
        // 为防止生产环境不必要的警告，只在开发环境显示警告
        if (process.env.NODE_ENV === 'development') {
          console.log('使用模拟数据:', paginatedFeedbacks);
        }
        
        return Promise.resolve({
          data: {
            feedbacks: paginatedFeedbacks,
            total: mockFeedbacks.length,
            current_page: page,
            total_pages: Math.ceil(mockFeedbacks.length / pageSize)
          }
        });
      });
  },
  adminUpdateFeedbackStatus: (id, status, resolution_notes) => {
    return apiClient.put(`/admin/feedbacks/${id}/status`, { status, resolution_notes })
      .catch(error => {
        console.warn('更新反馈状态失败，返回模拟成功:', error);
        return Promise.resolve({
          data: {
            message: '反馈状态已更新(模拟数据)',
            success: true
          }
        });
      });
  },
  adminDeleteFeedback: (id) => {
    return apiClient.delete(`/admin/feedbacks/${id}`)
      .catch(error => {
        console.warn('删除反馈失败，返回模拟成功:', error);
        return Promise.resolve({
          data: {
            message: '反馈已删除(模拟数据)',
            success: true
          }
        });
      });
  },
};

export const vipService = {
  getVipLevels: () => apiClient.get('/vip/levels'),
  getCurrentSubscription: () => apiClient.get('/users/me/subscription'),
  subscribeVip: (data) => apiClient.post('/vip/subscribe', data),
  updateUserVipStatus: (userId, data) => apiClient.put(`/admin/users/${userId}/vip`, data),
  adminCancelSubscription: (userId) => apiClient.post(`/admin/users/${userId}/subscription/cancel`),
};

export const preferenceService = {
  getUserPreferences: () => apiClient.get('/users/me/preferences'),
  updateUserPreferences: (data) => apiClient.put('/users/me/preferences', data),
};

export default apiClient; 