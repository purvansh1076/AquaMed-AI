import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

interface AlertBoxProps {
  type?: 'error' | 'warning' | 'info' | 'success';
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export const AlertBox: React.FC<AlertBoxProps> = ({
  type = 'info',
  title,
  message,
}) => {
  const getIcon = () => {
    switch (type) {
      case 'error':
        return <AlertCircle size={18} style={{ color: 'var(--status-error)', flexShrink: 0 }} />;
      case 'warning':
        return <AlertTriangle size={18} style={{ color: 'var(--status-warning)', flexShrink: 0 }} />;
      case 'success':
        return <CheckCircle2 size={18} style={{ color: 'var(--status-success)', flexShrink: 0 }} />;
      default:
        return <Info size={18} style={{ color: 'var(--status-info)', flexShrink: 0 }} />;
    }
  };

  return (
    <div className={`alert alert-${type}`}>
      {getIcon()}
      <div style={{ flex: 1 }}>
        {title && <div style={{ fontWeight: 600, marginBottom: '2px' }}>{title}</div>}
        <div>{message}</div>
      </div>
    </div>
  );
};
