import React from 'react';

const Permission: React.FC = () => {
  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: 400 }}>
      <h2 style={{ fontWeight: 600, fontSize: 20, marginBottom: 16 }}>权限管理</h2>
      <p>这里将展示角色列表、权限分配、子账号管理等功能。</p>
      {/* 后续可扩展为表格、表单、权限树等 */}
    </div>
  );
};

export default Permission; 