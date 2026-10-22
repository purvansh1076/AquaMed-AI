/**
 * AquaMediAI — Conflict Grouping Utility
 * Groups conflict entries into intuitive, human-understandable categories
 * for both Farmer View and Expert View.
 */

export interface GroupedConflict {
  key: 'water_shortage' | 'timing_conflict' | 'canal_capacity' | 'crop_stress' | 'minimum_requirement';
  farmerTitle: string;
  farmerTitleKey: string;
  farmerExplanationKey: string;
  expertTitle: string;
  expertExplanation: string;
  technicalCode: string;
  count: number;
  severities: string[];
  highestSeverity: string;
  totalResourceGapM3: number;
  involvedFarmers: string[];
  rationales: string[];
}

export function groupConflicts(
  conflicts: Array<{
    conflict_type?: string;
    severity?: string;
    resource_gap_m3?: number;
    involved_farmer_ids?: string[];
    explanation?: string;
    rationale?: string;
  }> = []
): GroupedConflict[] {
  const groups: Record<string, GroupedConflict> = {};

  const getCategoryKey = (type: string = ''): GroupedConflict['key'] => {
    const lower = type.toLowerCase();
    if (lower.includes('shortage') || lower.includes('deficit') || lower.includes('water')) {
      return 'water_shortage';
    }
    if (lower.includes('window') || lower.includes('overlap') || lower.includes('timing')) {
      return 'timing_conflict';
    }
    if (lower.includes('canal') || lower.includes('capacity')) {
      return 'canal_capacity';
    }
    if (lower.includes('stress') || lower.includes('urgency') || lower.includes('crop')) {
      return 'crop_stress';
    }
    return 'minimum_requirement';
  };

  const getCategoryMeta = (key: GroupedConflict['key']) => {
    switch (key) {
      case 'water_shortage': {
        return {
          farmerTitle: 'Water Shortage',
          farmerTitleKey: 'conflictWaterShortage',
          farmerExplanationKey: 'conflictWaterShortageDesc',
          expertTitle: 'Volumetric Water Shortage',
          expertExplanation: 'Total water available was lower than total farmer demand.',
          technicalCode: 'RESOURCE_SHORTAGE',
        };
      }
      case 'timing_conflict': {
        return {
          farmerTitle: 'Overlapping Schedules',
          farmerTitleKey: 'conflictWindowOverlap',
          farmerExplanationKey: 'conflictWindowOverlapDesc',
          expertTitle: 'Irrigation Window Timing Overlap',
          expertExplanation: 'Some farmers needed water during overlapping irrigation periods.',
          technicalCode: 'IRRIGATION_WINDOW_OVERLAP',
        };
      }
      case 'canal_capacity': {
        return {
          farmerTitle: 'Canal Capacity',
          farmerTitleKey: 'conflictCanalCapacity',
          farmerExplanationKey: 'conflictCanalCapacityDesc',
          expertTitle: 'Canal Delivery Limit',
          expertExplanation: 'The canal could not provide unlimited water at the same time.',
          technicalCode: 'CANAL_CAPACITY_LIMIT',
        };
      }
      case 'crop_stress': {
        return {
          farmerTitle: 'Water Priority',
          farmerTitleKey: 'conflictHighCropStress',
          farmerExplanationKey: 'conflictHighCropStressDesc',
          expertTitle: 'Crop Water Stress',
          expertExplanation: 'Some crops had higher water requirements at their growth stage.',
          technicalCode: 'HIGH_CROP_WATER_STRESS',
        };
      }
      case 'minimum_requirement': {
        return {
          farmerTitle: 'Minimum Requirement',
          farmerTitleKey: 'conflictMinRequirement',
          farmerExplanationKey: 'conflictMinRequirementDesc',
          expertTitle: 'Minimum Constraint',
          expertExplanation: 'The system considered minimum water requirements while allocating available water.',
          technicalCode: 'MINIMUM_REQUIREMENT_DEFICIT',
        };
      }
    }
  };

  for (const c of conflicts) {
    const key = getCategoryKey(c.conflict_type);
    if (!groups[key]) {
      const meta = getCategoryMeta(key);
      groups[key] = {
        key,
        farmerTitle: meta.farmerTitle,
        farmerTitleKey: meta.farmerTitleKey,
        farmerExplanationKey: meta.farmerExplanationKey,
        expertTitle: meta.expertTitle,
        expertExplanation: meta.expertExplanation,
        technicalCode: meta.technicalCode,
        count: 0,
        severities: [],
        highestSeverity: 'low',
        totalResourceGapM3: 0,
        involvedFarmers: [],
        rationales: [],
      };
    }

    const g = groups[key];
    g.count += 1;
    if (c.severity) {
      g.severities.push(c.severity.toUpperCase());
      const s = c.severity.toLowerCase();
      if (s === 'critical') g.highestSeverity = 'CRITICAL';
      else if (s === 'high' && g.highestSeverity !== 'CRITICAL') g.highestSeverity = 'HIGH';
      else if (s === 'medium' && !['CRITICAL', 'HIGH'].includes(g.highestSeverity)) g.highestSeverity = 'MEDIUM';
    }
    if (c.resource_gap_m3) {
      g.totalResourceGapM3 += c.resource_gap_m3;
    }
    if (c.involved_farmer_ids) {
      for (const id of c.involved_farmer_ids) {
        if (!g.involvedFarmers.includes(id)) {
          g.involvedFarmers.push(id);
        }
      }
    }
    const rat = c.explanation || c.rationale;
    if (rat && !g.rationales.includes(rat)) {
      g.rationales.push(rat);
    }
  }

  return Object.values(groups);
}