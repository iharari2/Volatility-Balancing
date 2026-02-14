import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { getPortfolioPositions, PositionSummaryItem } from '../../api/cockpit';

export type WorkspaceTab = 'overview' | 'trading' | 'events' | 'strategy' | 'explainability' | 'orders' | 'dividends';
export type PositionFilter = 'all' | 'active' | 'paused';

interface Position extends PositionSummaryItem {
  // Extended position type for workspace
}

interface WorkspaceContextType {
  // Portfolio state (from TenantPortfolioContext)
  portfolioId: string | null;
  setPortfolioId: (id: string | null) => void;

  // Position state
  positions: Position[];
  positionsLoading: boolean;
  selectedPositionId: string | null;
  setSelectedPositionId: (id: string | null) => void;
  selectedPosition: Position | null;

  // Filter state
  positionFilter: PositionFilter;
  setPositionFilter: (filter: PositionFilter) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredPositions: Position[];

  // Tab state
  activeTab: WorkspaceTab;
  setActiveTab: (tab: WorkspaceTab) => void;

  // Refresh
  refreshPositions: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within WorkspaceProvider');
  }
  return context;
}

interface WorkspaceProviderProps {
  children: ReactNode;
}

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const { selectedPortfolioId, setSelectedPortfolioId, selectedTenantId } = useTenantPortfolio();

  // Position state
  const [positions, setPositions] = useState<Position[]>([]);
  const [positionsLoading, setPositionsLoading] = useState(false);
  const [selectedPositionId, setSelectedPositionIdState] = useState<string | null>(
    searchParams.get('position')
  );

  // Filter state
  const [positionFilter, setPositionFilter] = useState<PositionFilter>(
    (searchParams.get('filter') as PositionFilter) || 'all'
  );
  const [searchQuery, setSearchQuery] = useState('');

  // Tab state
  const [activeTab, setActiveTabState] = useState<WorkspaceTab>(
    (searchParams.get('tab') as WorkspaceTab) || 'overview'
  );

  // Sync URL params
  const updateSearchParams = useCallback(
    (updates: Record<string, string | null>) => {
      setSearchParams((prev) => {
        const newParams = new URLSearchParams(prev);
        Object.entries(updates).forEach(([key, value]) => {
          if (value) {
            newParams.set(key, value);
          } else {
            newParams.delete(key);
          }
        });
        return newParams;
      });
    },
    [setSearchParams]
  );

  // Portfolio ID setter that updates URL
  const setPortfolioId = useCallback(
    (id: string | null) => {
      setSelectedPortfolioId(id || '');
      updateSearchParams({ portfolio: id });
    },
    [setSelectedPortfolioId, updateSearchParams]
  );

  // Position ID setter that updates URL
  const setSelectedPositionId = useCallback(
    (id: string | null) => {
      setSelectedPositionIdState(id);
      updateSearchParams({ position: id });
    },
    [updateSearchParams]
  );

  // Tab setter that updates URL
  const setActiveTab = useCallback(
    (tab: WorkspaceTab) => {
      setActiveTabState(tab);
      updateSearchParams({ tab });
    },
    [updateSearchParams]
  );

  // Filter setter that updates URL
  const setPositionFilterWithUrl = useCallback(
    (filter: PositionFilter) => {
      setPositionFilter(filter);
      updateSearchParams({ filter: filter === 'all' ? null : filter });
    },
    [updateSearchParams]
  );

  // Load positions when portfolio changes
  const loadPositions = useCallback(async () => {
    if (!selectedPortfolioId) {
      setPositions([]);
      return;
    }

    try {
      setPositionsLoading(true);
      const data = await getPortfolioPositions(selectedPortfolioId);
      setPositions(data);

      // Auto-select first position if none selected
      if (data.length > 0 && !selectedPositionId) {
        setSelectedPositionId(data[0].position_id);
      }
    } catch (error) {
      console.error('Error loading positions:', error);
      setPositions([]);
    } finally {
      setPositionsLoading(false);
    }
  }, [selectedPortfolioId, selectedPositionId, setSelectedPositionId]);

  useEffect(() => {
    loadPositions();
  }, [selectedPortfolioId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync from URL on mount
  useEffect(() => {
    const portfolioFromUrl = searchParams.get('portfolio');
    const positionFromUrl = searchParams.get('position');
    const tabFromUrl = searchParams.get('tab') as WorkspaceTab;
    const filterFromUrl = searchParams.get('filter') as PositionFilter;

    if (portfolioFromUrl && portfolioFromUrl !== selectedPortfolioId) {
      setSelectedPortfolioId(portfolioFromUrl);
    }
    if (positionFromUrl) {
      setSelectedPositionIdState(positionFromUrl);
    }
    if (tabFromUrl && ['overview', 'trading', 'events', 'strategy', 'explainability', 'orders', 'dividends'].includes(tabFromUrl)) {
      setActiveTabState(tabFromUrl);
    }
    if (filterFromUrl && ['all', 'active', 'paused'].includes(filterFromUrl)) {
      setPositionFilter(filterFromUrl);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Computed values
  const selectedPosition = positions.find((p) => p.position_id === selectedPositionId) || null;

  const filteredPositions = positions.filter((p) => {
    // Filter by status
    if (positionFilter === 'active' && p.status !== 'RUNNING') return false;
    if (positionFilter === 'paused' && p.status !== 'PAUSED') return false;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return p.asset_symbol.toLowerCase().includes(query);
    }

    return true;
  });

  const value: WorkspaceContextType = {
    portfolioId: selectedPortfolioId,
    setPortfolioId,
    positions,
    positionsLoading,
    selectedPositionId,
    setSelectedPositionId,
    selectedPosition,
    positionFilter,
    setPositionFilter: setPositionFilterWithUrl,
    searchQuery,
    setSearchQuery,
    filteredPositions,
    activeTab,
    setActiveTab,
    refreshPositions: loadPositions,
  };

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}
