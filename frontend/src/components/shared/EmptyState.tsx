import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Plus } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    to?: string;
    onClick?: () => void;
  };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  const defaultIcon = <Briefcase className="h-16 w-16 text-gray-400" />;

  const actionButton = action && (
    <div className="mt-6">
      {action.to ? (
        <Link
          to={action.to}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="h-5 w-5 mr-2" />
          {action.label}
        </Link>
      ) : (
        <button
          onClick={action.onClick}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="h-5 w-5 mr-2" />
          {action.label}
        </button>
      )}
    </div>
  );

  return (
    <div className="text-center py-12">
      <div className="mx-auto flex justify-center">{icon || defaultIcon}</div>
      <h3 className="mt-4 text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">{description}</p>
      {actionButton}
    </div>
  );
}









