import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../src/pages/Login';

describe('登录页', () => {
  it('渲染登录表单', () => {
    render(<Login onLogin={() => {}} />);
    expect(screen.getByText('库存管理系统')).toBeInTheDocument();
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument();
    expect(screen.getByLabelText('用户名')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('表单校验：未输入时提示', async () => {
    render(<Login onLogin={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: '登录' }));
    await waitFor(() => {
      expect(screen.getByText('请输入有效邮箱')).toBeInTheDocument();
      expect(screen.getByText('请输入用户名')).toBeInTheDocument();
      expect(screen.getByText('请输入密码')).toBeInTheDocument();
    });
  });

  it('登录成功回调', async () => {
    const mockLogin = jest.fn();
    // mock axios
    jest.spyOn(global, 'fetch').mockImplementation((url, options) => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ access_token: 'token', user: { username: 'admin' } })
      }) as any;
    });
    render(<Login onLogin={mockLogin} />);
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('token', { username: 'admin' });
    });
    (global.fetch as any).mockRestore();
  });
}); 