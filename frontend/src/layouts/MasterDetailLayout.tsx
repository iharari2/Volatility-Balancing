import { ReactNode, useState } from 'react';
import { Menu, X, ChevronLeft, ChevronRight } from 'lucide-react';

interface MasterDetailLayoutProps {
  topBar: ReactNode;
  leftPanel: ReactNode;
  rightPanel: ReactNode;
  leftPanelWidth?: number;
  minLeftPanelWidth?: number;
  maxLeftPanelWidth?: number;
}

export default function MasterDetailLayout({
  topBar,
  leftPanel,
  rightPanel,
  leftPanelWidth = 320,
  minLeftPanelWidth = 280,
  maxLeftPanelWidth = 480,
}: MasterDetailLayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [panelWidth, setPanelWidth] = useState(leftPanelWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);

    const startX = e.clientX;
    const startWidth = panelWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const delta = e.clientX - startX;
      const newWidth = Math.max(minLeftPanelWidth, Math.min(maxLeftPanelWidth, startWidth + delta));
      setPanelWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Bar - 56px */}
      <header className="h-14 shrink-0 border-b border-gray-200 bg-white sticky top-0 z-40">
        <div className="h-full flex items-center px-4">
          {/* Mobile menu button */}
          <button
            type="button"
            className="p-2 -ml-2 text-gray-500 hover:text-gray-700 lg:hidden"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>
          {topBar}
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Mobile overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 z-50 bg-gray-600 bg-opacity-50 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Left Panel (Master) */}
        <aside
          className={`
            ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
            fixed inset-y-0 left-0 z-50 bg-white border-r border-gray-200 transition-transform duration-300
            lg:relative lg:translate-x-0 lg:transition-none
            ${isCollapsed ? 'lg:w-0 lg:border-r-0' : ''}
          `}
          style={{
            width: mobileMenuOpen ? '100%' : isCollapsed ? 0 : panelWidth,
            maxWidth: mobileMenuOpen ? '320px' : undefined,
          }}
        >
          {/* Mobile close button */}
          <button
            type="button"
            className="absolute top-4 right-4 p-1 text-gray-500 hover:text-gray-700 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>

          {/* Left panel content */}
          <div className={`h-full overflow-hidden ${isCollapsed ? 'lg:hidden' : ''}`}>
            {leftPanel}
          </div>

          {/* Resize handle - desktop only */}
          {!isCollapsed && (
            <div
              className="hidden lg:block absolute top-0 right-0 w-1 h-full cursor-col-resize bg-transparent hover:bg-primary-300 transition-colors"
              onMouseDown={handleMouseDown}
              style={{ cursor: isResizing ? 'col-resize' : undefined }}
            />
          )}
        </aside>

        {/* Collapse/Expand toggle - desktop only */}
        <button
          type="button"
          className="hidden lg:flex absolute left-0 top-1/2 -translate-y-1/2 z-30 h-16 w-4 items-center justify-center bg-gray-100 hover:bg-gray-200 border border-l-0 border-gray-200 rounded-r transition-colors"
          style={{ left: isCollapsed ? 0 : panelWidth }}
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronLeft className="h-4 w-4 text-gray-500" />
          )}
        </button>

        {/* Right Panel (Detail) */}
        <main
          className="flex-1 overflow-auto bg-gray-50"
          style={{ marginLeft: isCollapsed ? '16px' : 0 }}
        >
          {rightPanel}
        </main>
      </div>
    </div>
  );
}
