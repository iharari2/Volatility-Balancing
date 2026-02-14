import { LayoutDashboard, Activity, Clock, Settings, Table2, ClipboardList, DollarSign } from 'lucide-react';
import { useWorkspace, WorkspaceTab } from '../../WorkspaceContext';

const tabs: { value: WorkspaceTab; label: string; icon: typeof LayoutDashboard }[] = [
  { value: 'overview', label: 'Overview', icon: LayoutDashboard },
  { value: 'trading', label: 'Trading', icon: Activity },
  { value: 'events', label: 'Events', icon: Clock },
  { value: 'strategy', label: 'Strategy', icon: Settings },
  { value: 'explainability', label: 'Explainability', icon: Table2 },
  { value: 'orders', label: 'Orders', icon: ClipboardList },
  { value: 'dividends', label: 'Dividends', icon: DollarSign },
];

export default function DetailTabBar() {
  const { activeTab, setActiveTab } = useWorkspace();

  return (
    <div className="border-b border-gray-200 bg-white">
      <div className="flex">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.value;
          const Icon = tab.icon;

          return (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
                isActive
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
