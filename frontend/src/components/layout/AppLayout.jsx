import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar, Topbar } from './Navigation';

const pageMeta = {
  '/': { title: 'Dashboard', subtitle: 'Overview of your license portfolio' },
  '/applications': { title: 'Applications', subtitle: 'Manage all registered applications' },
  '/products': { title: 'Products', subtitle: 'Product catalog across applications' },
  '/licenses': { title: 'Licenses', subtitle: 'License inventory and assignments' },
  '/sync': { title: 'Sync Jobs', subtitle: 'Data synchronization history and status' },
  '/settings': { title: 'Settings', subtitle: 'Portal configuration' },
};

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { pathname } = useLocation();
  const meta = pageMeta[pathname] || { title: 'License Portal', subtitle: '' };

  return (
    <div className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      <div className={`main-area ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <Topbar collapsed={collapsed} title={meta.title} subtitle={meta.subtitle} />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
