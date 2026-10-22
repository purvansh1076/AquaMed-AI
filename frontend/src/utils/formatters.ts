/**
 * Utility functions for formatting numbers, water metrics, percentages, and labels.
 */

export function formatWater(m3: number | null | undefined): string {
  if (m3 === null || m3 === undefined || isNaN(m3)) return '—';
  return `${m3.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} m³`;
}

export function formatPercent(ratio: number | null | undefined, decimals = 1): string {
  if (ratio === null || ratio === undefined || isNaN(ratio)) return '—';
  return `${(ratio * 100).toFixed(decimals)}%`;
}

export function formatDecimal(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return val.toFixed(decimals);
}

export function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

export function getSeverityClass(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'badge-critical';
    case 'high':
      return 'badge-high';
    case 'medium':
      return 'badge-medium';
    case 'low':
      return 'badge-low';
    default:
      return 'badge-neutral';
  }
}

export function getStatusClass(status: string): string {
  switch (status?.toLowerCase()) {
    case 'agreed':
    case 'optimal':
    case 'satisfied':
    case 'healthy':
      return 'status-success';
    case 'max_rounds_reached':
    case 'relaxed':
    case 'degraded':
      return 'status-warning';
    case 'no_feasible_improvement':
    case 'failed':
    case 'violated':
      return 'status-error';
    default:
      return 'status-neutral';
  }
}
