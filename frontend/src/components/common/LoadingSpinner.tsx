import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  subMessage?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Processing request...',
  subMessage,
}) => {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <div style={{ textAlign: 'center' }}>
        <p style={{ fontWeight: 600, color: 'var(--color-primary-dark)', fontSize: '15px' }}>
          {message}
        </p>
        {subMessage && (
          <p style={{ color: 'var(--text-subtle)', fontSize: '12px', marginTop: '4px' }}>
            {subMessage}
          </p>
        )}
      </div>
    </div>
  );
};
