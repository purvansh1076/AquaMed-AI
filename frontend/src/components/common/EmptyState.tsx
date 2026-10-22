import React from 'react';
import { Link } from 'react-router-dom';
import { Database, ArrowRight } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  actionHref?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Scenario Loaded',
  description = 'Configure a scenario and run AquaMediAI to view results.',
  actionText = 'Configure Scenario',
  actionHref = '/scenario',
}) => {
  return (
    <div className="empty-state">
      <Database className="empty-state-icon" />
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-desc">{description}</p>
      {actionHref && (
        <Link to={actionHref} className="btn btn-primary">
          {actionText}
          <ArrowRight size={16} />
        </Link>
      )}
    </div>
  );
};
