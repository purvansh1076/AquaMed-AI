import React, { useState } from 'react';
import { Copy, Check, Download } from 'lucide-react';

interface RawJsonViewerProps {
  data: unknown;
  title?: string;
}

export const RawJsonViewer: React.FC<RawJsonViewerProps> = ({
  data,
  title = 'Raw API Response Payload',
}) => {
  const [copied, setCopied] = useState(false);
  const jsonString = JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aquamedi_scenario_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <div className="card-header">
        <div>
          <div className="card-title">{title}</div>
          <div className="card-subtitle">
            Verifiable, un-mutated JSON data directly from FastAPI backend
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button type="button" onClick={handleCopy} className="btn btn-outline btn-sm">
            {copied ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy JSON'}
          </button>
          <button type="button" onClick={handleDownload} className="btn btn-outline btn-sm">
            <Download size={14} />
            Export JSON
          </button>
        </div>
      </div>
      <pre
        style={{
          backgroundColor: '#0f172a',
          color: '#e2e8f0',
          padding: '16px',
          borderRadius: '6px',
          overflowX: 'auto',
          maxHeight: '480px',
          fontSize: '12px',
          fontFamily: 'monospace',
          lineHeight: '1.4',
        }}
      >
        {jsonString}
      </pre>
    </div>
  );
};
