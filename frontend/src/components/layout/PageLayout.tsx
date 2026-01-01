import { ReactNode, useState } from 'react';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import { Menu } from 'lucide-react';

interface PageLayoutProps {
  children: ReactNode;
  mode?: 'Live' | 'Simulation' | 'Sandbox';
}

export default function PageLayout({ children, mode }: PageLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar mode={mode} />

      <Sidebar mobileOpen={sidebarOpen} onMobileClose={() => setSidebarOpen(false)} />

      {/* Mobile menu button */}
      <button
        type="button"
        className="fixed top-4 left-4 z-50 -m-2.5 p-2.5 text-gray-700 lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <Menu className="h-6 w-6" />
      </button>

      {/* Main content */}
      <div className="lg:pl-64">
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
















