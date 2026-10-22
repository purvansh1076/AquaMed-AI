import type { ReasonCode } from '../types/api';

export interface ReasonCodeMeta {
  label: string;
  category: 'scarcity' | 'agronomic' | 'constraint' | 'negotiation' | 'satisfaction';
  description: string;
  badgeClass: string;
}

export const REASON_CODE_METAS: Record<ReasonCode, ReasonCodeMeta> = {
  RESOURCE_SHORTAGE: {
    label: 'Resource Shortage',
    category: 'scarcity',
    description: 'Total requested demand exceeds available canal water.',
    badgeClass: 'badge-critical',
  },
  WATER_SURPLUS: {
    label: 'Water Surplus',
    category: 'scarcity',
    description: 'Available supply exceeds total demand, allowing full allocation.',
    badgeClass: 'badge-success',
  },
  HIGH_URGENCY: {
    label: 'High Crop Urgency',
    category: 'agronomic',
    description: 'Farmer urgency score > 0.70; prioritised during scarce allocation.',
    badgeClass: 'badge-high',
  },
  HIGH_CROP_SENSITIVITY: {
    label: 'High Crop Sensitivity',
    category: 'agronomic',
    description: 'Crop sensitivity Ky > 0.80; high yield impact if deficit occurs.',
    badgeClass: 'badge-high',
  },
  MINIMUM_REQUIREMENT: {
    label: 'Minimum Requirement Protected',
    category: 'constraint',
    description: 'Allocation covers survival water threshold (FAO-56 floor).',
    badgeClass: 'badge-info',
  },
  MAXIMUM_REQUIREMENT: {
    label: 'Maximum Requirement Bound',
    category: 'constraint',
    description: 'Allocation bounded by upper canal and soil intake limits.',
    badgeClass: 'badge-neutral',
  },
  CANAL_CAPACITY: {
    label: 'Canal Capacity Bound',
    category: 'constraint',
    description: 'Delivery constrained by physical flow rate of the canal branch.',
    badgeClass: 'badge-warning',
  },
  WINDOW_CONFLICT: {
    label: 'Window Conflict',
    category: 'constraint',
    description: 'Overlapping irrigation schedules required operational adjustments.',
    badgeClass: 'badge-warning',
  },
  FAIRNESS_ADJUSTMENT: {
    label: 'Fairness Adjustment',
    category: 'negotiation',
    description: 'Allocation balances satisfaction distribution across agents.',
    badgeClass: 'badge-info',
  },
  NEGOTIATION_CONCESSION: {
    label: 'Negotiation Concession',
    category: 'negotiation',
    description: 'Farmer agreed to reduce ask to facilitate collective agreement.',
    badgeClass: 'badge-info',
  },
  BATNA_PROTECTION: {
    label: 'BATNA Protection',
    category: 'negotiation',
    description: 'Farmer rejected proposal below minimum survival alternative.',
    badgeClass: 'badge-warning',
  },
  UNMET_DEMAND: {
    label: 'Unmet Water Demand',
    category: 'satisfaction',
    description: 'Allocated volume is less than predicted optimal agronomic requirement.',
    badgeClass: 'badge-warning',
  },
  FULL_DEMAND_SATISFACTION: {
    label: 'Full Demand Satisfied',
    category: 'satisfaction',
    description: '100% of the farmer’s predicted water demand was allocated.',
    badgeClass: 'badge-success',
  },
};

export function getReasonCodeMeta(code: string): ReasonCodeMeta {
  const meta = REASON_CODE_METAS[code as ReasonCode];
  if (meta) return meta;
  return {
    label: code.replace(/_/g, ' '),
    category: 'scarcity',
    description: 'System reason code',
    badgeClass: 'badge-neutral',
  };
}
