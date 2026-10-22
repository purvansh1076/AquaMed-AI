import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MetricCard } from '../components/common/MetricCard';
import { Badge } from '../components/common/Badge';
import { AlertBox } from '../components/common/AlertBox';
import { EmptyState } from '../components/common/EmptyState';
import { PipelineStepper } from '../components/pipeline/PipelineStepper';
import { FarmerAllocationTable } from '../components/tables/FarmerAllocationTable';
import { ConflictListTable } from '../components/tables/ConflictListTable';
import { ConcessionTable } from '../components/tables/ConcessionTable';
import { formatWater, formatPercent, capitalize } from '../utils/formatters';
import type { FarmerAllocationResponse, ConflictReportResponse, ConcessionResponse } from '../types/api';

describe('Common Components & Formatters', () => {
  it('formatters work correctly for water volume and percentages', () => {
    expect(formatWater(123.456)).toBe('123.5 m³');
    expect(formatWater(null)).toBe('—');
    expect(formatPercent(0.8523)).toBe('85.2%');
    expect(formatPercent(null)).toBe('—');
    expect(capitalize('severe_shortage')).toBe('Severe shortage');
  });

  it('MetricCard renders label, value, and footnote', () => {
    render(
      <MetricCard
        label="Available Water"
        value="500.0"
        unit="m³"
        footnote="Canal head supply"
      />
    );
    expect(screen.getByText('Available Water')).toBeInTheDocument();
    expect(screen.getByText('500.0')).toBeInTheDocument();
    expect(screen.getByText('m³')).toBeInTheDocument();
    expect(screen.getByText('Canal head supply')).toBeInTheDocument();
  });

  it('Badge renders correct variant class', () => {
    const { container } = render(<Badge variant="critical">CRITICAL</Badge>);
    expect(container.querySelector('.badge-critical')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('AlertBox displays message and title', () => {
    render(<AlertBox type="warning" title="Warning Note" message="Low water level" />);
    expect(screen.getByText('Warning Note')).toBeInTheDocument();
    expect(screen.getByText('Low water level')).toBeInTheDocument();
  });

  it('EmptyState renders with CTA link', () => {
    render(
      <MemoryRouter>
        <EmptyState
          title="Custom Empty State"
          description="Please take action"
          actionText="Click Here"
          actionHref="/test"
        />
      </MemoryRouter>
    );
    expect(screen.getByText('Custom Empty State')).toBeInTheDocument();
    expect(screen.getByText('Please take action')).toBeInTheDocument();
    expect(screen.getByText('Click Here')).toBeInTheDocument();
  });

  it('PipelineStepper displays all 6 pipeline stages in idle state when result is null', () => {
    render(<PipelineStepper scenarioResult={null} />);
    expect(screen.getByText('Demand Prediction')).toBeInTheDocument();
    expect(screen.getByText('Conflict Detection')).toBeInTheDocument();
    expect(screen.getByText('Water Optimization')).toBeInTheDocument();
    expect(screen.getByText('Multi-Agent Negotiation')).toBeInTheDocument();
    expect(screen.getByText('Explainability')).toBeInTheDocument();
    expect(screen.getByText('Final Agreement')).toBeInTheDocument();
  });

  it('FarmerAllocationTable renders rows and satisfaction values', () => {
    const mockAllocations: FarmerAllocationResponse[] = [
      {
        farmer_id: 'FARM_0001',
        crop: 'wheat',
        growth_stage: 'germination',
        urgency: 0.85,
        crop_sensitivity: 0.9,
        predicted_demand_m3: 150,
        minimum_requirement_m3: 75,
        maximum_requirement_m3: 200,
        allocated_water_m3: 150,
        unmet_demand_m3: 0,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 1.0,
        constraint_status: 'satisfied',
      },
    ];

    render(<FarmerAllocationTable allocations={mockAllocations} />);
    expect(screen.getByText('FARM_0001')).toBeInTheDocument();
    expect(screen.getByText('Wheat')).toBeInTheDocument();
    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });

  it('ConflictListTable renders conflicts and empty message when empty', () => {
    const { rerender } = render(<ConflictListTable conflicts={[]} />);
    expect(screen.getByText(/No operational or resource conflicts detected/)).toBeInTheDocument();

    const mockConflicts: ConflictReportResponse[] = [
      {
        conflict_id: 'conf_1',
        conflict_type: 'resource_shortage',
        severity: 'high',
        severity_score: 0.8,
        involved_farmer_ids: ['FARM_0001', 'FARM_0002'],
        available_water_m3: 300,
        total_demand_m3: 400,
        resource_gap_m3: 100,
        explanation: 'Demand exceeds supply by 100 m³',
      },
    ];

    rerender(<ConflictListTable conflicts={mockConflicts} />);
    expect(screen.getByText('RESOURCE SHORTAGE')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('Demand exceeds supply by 100 m³')).toBeInTheDocument();
  });

  it('ConcessionTable renders concessions records', () => {
    const mockConcessions: ConcessionResponse[] = [
      {
        farmer_id: 'FARM_0002',
        round_number: 1,
        previous_ask_m3: 180,
        new_ask_m3: 160,
        concession_amount_m3: 20,
        concession_ratio: 0.11,
        flexibility_factor: 0.7,
        urgency_factor: 0.3,
        reason: 'Conceded 20 m³',
      },
    ];

    render(<ConcessionTable concessions={mockConcessions} />);
    expect(screen.getByText('R1')).toBeInTheDocument();
    expect(screen.getByText('FARM_0002')).toBeInTheDocument();
    expect(screen.getByText('Conceded 20 m³')).toBeInTheDocument();
  });
});
