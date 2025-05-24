import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Product from './Product';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('商品管理页面', () => {
  beforeEach(() => {
    mockedAxios.get.mockResolvedValue({ data: [] });
  });

  it('渲染商品列表', async () => {
    render(<Product />);
    expect(screen.getByText('新增商品')).toBeInTheDocument();
    await waitFor(() => expect(mockedAxios.get).toHaveBeenCalled());
  });

  it('新增商品流程', async () => {
    render(<Product />);
    fireEvent.click(screen.getByText('新增商品'));
    fireEvent.change(screen.getByLabelText('商品名称'), { target: { value: '测试商品' } });
    fireEvent.change(screen.getByLabelText('SKU'), { target: { value: 'SKU001' } });
    fireEvent.change(screen.getByLabelText('单位'), { target: { value: '件' } });
    fireEvent.change(screen.getByLabelText('状态'), { target: { value: '1' } });
    mockedAxios.post.mockResolvedValue({ data: { msg: '创建成功', id: 1 } });
    fireEvent.click(screen.getByText('确定'));
    await waitFor(() => expect(mockedAxios.post).toHaveBeenCalled());
  });
}); 