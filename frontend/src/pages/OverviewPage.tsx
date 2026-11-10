/**
 * AquaMedi AI — Water Distribution Dashboard & Administrative Overview
 * ====================================================================
 * Formal government-style agricultural water management portal.
 * Clean white/light backgrounds, navy (#12315B) & government green (#176B45).
 * Replaces illustrative GIS with administrative tables and analytical charts.
 */

import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Droplets,
  Scale,
  AlertOctagon,
  ArrowRight,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  Download,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useScenario } from '../context/ScenarioContext';
import { MetricCard } from '../components/common/MetricCard';
import { PipelineStepper } from '../components/pipeline/PipelineStepper';
import { EmptyState } from '../components/common/EmptyState';
import { formatWater, formatPercent, capitalize } from '../utils/formatters';
import type { FarmerAllocationResponse } from '../types/api';

// Standard Indian farmer names mapped deterministically for demonstration
const FARMER_NAMES: Record<string, string> = {
  FARM_0001: 'Ramesh Patil',
  FARM_0002: 'Suresh Deshmukh',
  FARM_0003: 'Anand Shinde',
  FARM_0004: 'Kishor Kale',
  FARM_0005: 'Sunil Jadhav',
  FARM_0006: 'Vikas More',
  FARM_0007: 'Babanrao Kadam',
  FARM_0008: 'Dnyaneshwar Pawar',
  FARM_0009: 'Pandurang Bhosale',
  FARM_0010: 'Ganesh Shingate',
  FARM_0011: 'Shivaji Jagtap',
  FARM_0012: 'Santosh Gaikwad',
  FARM_0013: 'Rajendra Thorat',
  FARM_0014: 'Ashok Chavan',
  FARM_0015: 'Mahadev Raut',
  FARM_0016: 'Nitin Sonawane',
  FARM_0017: 'Balasaheb Tambe',
  FARM_0018: 'Gorakh Gite',
  FARM_0019: 'Sambhaji Kolhe',
  FARM_0020: 'Navnath Vikhe',
};

// Table row data structure derived from executed scenario allocations
interface TableRowData {
  farmer_id: string;
  farmer_name: string;
  crop: string;
  area_ha: number;
  requested_m3: number;
  allocated_m3: number;
  deficit_m3: number;
  status: 'Adequate' | 'Partial' | 'Shortage';
  reach: 'Head-Reach' | 'Middle-Reach' | 'Tail-Reach';
}

export const OverviewPage: React.FC = () => {
  const { scenarioResult } = useScenario();
  const [filterReach, setFilterReach] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Extract allocations list from active scenario result
  const allocations: FarmerAllocationResponse[] = useMemo(() => {
    return scenarioResult?.initial_allocation?.allocations || [];
  }, [scenarioResult]);

  // Compute table data strictly from active scenario; returns empty array when no scenario is loaded
  const tableData: TableRowData[] = useMemo(() => {
    if (!scenarioResult || allocations.length === 0) return [];

    return allocations.map((alloc, idx) => {
      const fid = alloc.farmer_id;
      const farmerName = FARMER_NAMES[fid] || `Farmer ${idx + 1}`;
      const crop = capitalize(alloc.crop || 'Field Crop');

      // Estimate area from prediction input summary if present
      const pred = scenarioResult.predictions?.find((p) => p.farmer_id === fid);
      const rawArea = Number(pred?.input_summary?.farm_area_hectares);
      const area_ha = !isNaN(rawArea) && rawArea > 0 ? Number(rawArea.toFixed(1)) : Number((1.5 + (idx % 4) * 0.7).toFixed(1));

      const requested_m3 = Number(alloc.predicted_demand_m3.toFixed(1));
      const allocated_m3 = Number(alloc.allocated_water_m3.toFixed(1));
      const deficit_m3 = Number(Math.max(0, requested_m3 - allocated_m3).toFixed(1));

      let status: 'Adequate' | 'Partial' | 'Shortage' = 'Adequate';
      if (allocated_m3 <= 0 || deficit_m3 > requested_m3 * 0.4) {
        status = 'Shortage';
      } else if (deficit_m3 > requested_m3 * 0.08) {
        status = 'Partial';
      }

      // Assign canal reach based on relative index position
      const reachPct = idx / Math.max(1, allocations.length - 1);
      const reach: 'Head-Reach' | 'Middle-Reach' | 'Tail-Reach' =
        reachPct <= 0.33 ? 'Head-Reach' : reachPct <= 0.66 ? 'Middle-Reach' : 'Tail-Reach';

      return {
        farmer_id: fid,
        farmer_name: farmerName,
        crop,
        area_ha,
        requested_m3,
        allocated_m3,
        deficit_m3,
        status,
        reach,
      };
    });
  }, [scenarioResult, allocations]);

  // Real operational aggregate metrics from executed scenario
  const totalAvailable = scenarioResult?.available_water_m3 ?? 0;
  const totalRequested = scenarioResult?.total_demand_m3 ?? 0;
  const totalAllocated = scenarioResult?.initial_allocation?.total_allocated_m3 ?? 0;
  const totalDeficit = Number(Math.max(0, totalRequested - totalAllocated).toFixed(1));
  const numFarmers = scenarioResult?.n_farmers ?? allocations.length;
  const affectedFarmers = tableData.filter((r) => r.deficit_m3 > 0).length;

  // Chart 1: Requested vs Allocated
  const requestedVsAllocatedData = useMemo(() => {
    if (!scenarioResult || tableData.length === 0) return [];
    return tableData.slice(0, 10).map((r) => ({
      name: r.farmer_id,
      farmer: r.farmer_name,
      Requested: r.requested_m3,
      Allocated: r.allocated_m3,
    }));
  }, [scenarioResult, tableData]);

  // Chart 2: Crop-wise water demand
  const cropWiseDemandData = useMemo(() => {
    if (!scenarioResult || tableData.length === 0) return [];
    const cropMap: Record<string, { requested: number; allocated: number }> = {};
    tableData.forEach((r) => {
      if (!cropMap[r.crop]) {
        cropMap[r.crop] = { requested: 0, allocated: 0 };
      }
      cropMap[r.crop].requested += r.requested_m3;
      cropMap[r.crop].allocated += r.allocated_m3;
    });
    return Object.entries(cropMap).map(([crop, vals]) => ({
      crop,
      Demand: Number(vals.requested.toFixed(1)),
      Allocated: Number(vals.allocated.toFixed(1)),
    }));
  }, [scenarioResult, tableData]);

  // Chart 3: Reach allocation
  const reachData = useMemo(() => {
    if (!scenarioResult || tableData.length === 0) return [];
    const reaches = ['Head-Reach', 'Middle-Reach', 'Tail-Reach'] as const;
    return reaches.map((reachName) => {
      const subset = tableData.filter((r) => r.reach === reachName);
      const req = subset.reduce((acc, r) => acc + r.requested_m3, 0);
      const alloc = subset.reduce((acc, r) => acc + r.allocated_m3, 0);
      const def = subset.reduce((acc, r) => acc + r.deficit_m3, 0);
      return {
        reach: reachName.replace('-Reach', ''),
        Requested: Number(req.toFixed(1)),
        Allocated: Number(alloc.toFixed(1)),
        Deficit: Number(def.toFixed(1)),
      };
    });
  }, [scenarioResult, tableData]);

  // Chart 4: Shortage status distribution
  const statusPieData = useMemo(() => {
    if (!scenarioResult || tableData.length === 0) return [];
    const adequate = tableData.filter((r) => r.status === 'Adequate').length;
    const partial = tableData.filter((r) => r.status === 'Partial').length;
    const shortage = tableData.filter((r) => r.status === 'Shortage').length;
    return [
      { name: 'Adequate', value: adequate, color: '#176B45' },
      { name: 'Partial', value: partial, color: '#C58B20' },
      { name: 'Shortage', value: shortage, color: '#B42318' },
    ].filter((d) => d.value > 0);
  }, [scenarioResult, tableData]);

  // Filtered rows for the table
  const filteredRows = useMemo(() => {
    return tableData.filter((r) => {
      if (filterReach !== 'all' && r.reach !== filterReach) return false;
      if (filterStatus !== 'all' && r.status !== filterStatus) return false;
      return true;
    });
  }, [tableData, filterReach, filterStatus]);

  // CSV Export for administrative reporting
  const handleExportCSV = () => {
    if (!scenarioResult || tableData.length === 0) return;
    const headers = [
      'Farmer ID',
      'Farmer Name',
      'Crop',
      'Farm Area (ha)',
      'Water Requested (m3)',
      'Water Allocated (m3)',
      'Water Deficit (m3)',
      'Canal Reach',
      'Allocation Status',
    ];
    const rows = filteredRows.map((r) => [
      r.farmer_id,
      `"${r.farmer_name}"`,
      r.crop,
      r.area_ha,
      r.requested_m3,
      r.allocated_m3,
      r.deficit_m3,
      r.reach,
      r.status,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `water_allocation_report_${scenarioResult.scenario_id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ── Clean Empty State: When scenarioResult is null, render ONLY the Empty State ──
  if (!scenarioResult) {
    return (
      <div style={{ maxWidth: '1280px', margin: '0 auto', paddingBottom: '32px' }}>
        {/* Page Header: Formal Government Banner */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-default)',
            borderLeft: '4px solid #12315B',
            padding: '16px 20px',
            marginBottom: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1
                className="page-title"
                style={{
                  fontSize: '20px',
                  fontWeight: 700,
                  color: '#12315B',
                  margin: 0,
                }}
              >
                Water Distribution Dashboard
              </h1>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '3px',
                  backgroundColor: '#fdf7eb',
                  color: '#C58B20',
                  border: '1px solid #f5dfb0',
                  textTransform: 'uppercase',
                }}
              >
                No Active Scenario
              </span>
            </div>
            <p
              className="page-description"
              style={{
                fontSize: '13px',
                color: 'var(--text-muted)',
                marginTop: '4px',
                marginBottom: 0,
              }}
            >
              <strong>Mediation Overview</strong> — No active water distribution scenario is loaded.
              Configure and run an agronomic scenario to inspect machine learning demand predictions,
              conflict detection, and OR-Tools linear programming water allocations.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Link
              to="/scenario"
              className="btn btn-primary btn-sm"
              style={{
                backgroundColor: '#12315B',
                borderColor: '#12315B',
                color: '#FFFFFF',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>Run New Scenario</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>

        {/* Stepper showing unexecuted state */}
        <PipelineStepper scenarioResult={null} />

        {/* Clean Empty State Notice */}
        <div style={{ marginTop: '20px' }}>
          <EmptyState
            title="No Scenario Loaded"
            description="No operational results are currently available. Configure an agronomic scenario and run AquaMediAI mediation to inspect decisions, optimization results, and explainability."
            actionText="Configure & Run Scenario"
            actionHref="/scenario"
          />
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', paddingBottom: '32px' }}>
      {/* ── Page Header: Formal Government Banner ── */}
      <div
        style={{
          background: '#ffffff',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid #12315B',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1
              className="page-title"
              style={{
                fontSize: '20px',
                fontWeight: 700,
                color: '#12315B',
                margin: 0,
              }}
            >
              Water Distribution Dashboard
            </h1>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '3px',
                backgroundColor: '#eaf5ef',
                color: '#176B45',
                border: '1px solid #b8e2cd',
                textTransform: 'uppercase',
              }}
            >
              Live Scenario Solved
            </span>
          </div>
          <p
            className="page-description"
            style={{
              fontSize: '13px',
              color: 'var(--text-muted)',
              marginTop: '4px',
              marginBottom: 0,
            }}
          >
            <strong>Mediation Overview</strong> — Scenario:{' '}
            <strong style={{ color: '#12315B' }}>{scenarioResult.scenario_id}</strong> (
            {capitalize(scenarioResult.scenario_type)})
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={handleExportCSV}
            className="btn btn-outline btn-sm"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              color: '#12315B',
              borderColor: '#D9E0E7',
              backgroundColor: '#FFFFFF',
            }}
          >
            <Download size={14} />
            <span>Export CSV</span>
          </button>
          <Link
            to="/scenario"
            className="btn btn-primary btn-sm"
            style={{
              backgroundColor: '#12315B',
              borderColor: '#12315B',
              color: '#FFFFFF',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>Change Scenario</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* ── Stepper ── */}
      <PipelineStepper scenarioResult={scenarioResult} />

      {/* ── Section 1: Executive KPI Summary Cards ── */}
      <div
        className="kpi-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <MetricCard
          label="Total Available Water"
          value={formatWater(totalAvailable)}
          footnote="Command canal supply"
          icon={<Droplets size={18} style={{ color: '#12315B' }} />}
        />
        <MetricCard
          label="Total Predicted Demand"
          value={formatWater(totalRequested)}
          footnote="Aggregated crop demand"
          icon={<TrendingDown size={18} style={{ color: '#176B45' }} />}
        />
        <MetricCard
          label="Total Allocated Water"
          value={formatWater(totalAllocated)}
          footnote={`Utilization: ${formatPercent(totalAllocated / Math.max(1, totalAvailable))}`}
          icon={<Scale size={18} style={{ color: '#12315B' }} />}
        />
        <MetricCard
          label="Estimated Water Deficit"
          value={formatWater(totalDeficit)}
          footnote={totalDeficit > 0 ? 'Shortfall requires mediation' : 'Zero deficit (adequate)'}
          icon={<AlertOctagon size={18} style={{ color: totalDeficit > 0 ? '#B42318' : '#176B45' }} />}
        />
        <MetricCard
          label="Participating Farmers"
          value={numFarmers}
          unit="farmers"
          footnote="Water user members"
          icon={<Users size={18} style={{ color: '#12315B' }} />}
        />
        <MetricCard
          label="Affected Farmers"
          value={affectedFarmers}
          unit="farmers"
          footnote={`${affectedFarmers} of ${numFarmers} face shortage`}
          icon={<AlertTriangle size={18} style={{ color: affectedFarmers > 0 ? '#C58B20' : '#176B45' }} />}
        />
      </div>

      {/* ── Section 2: Water Allocation Table ── */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-default)',
          marginBottom: '24px',
          borderRadius: '4px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '14px 18px',
            backgroundColor: '#F5F7F9',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div>
            <h2
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: '#12315B',
                margin: 0,
              }}
            >
              Water Allocation Register
            </h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Farmer-by-farmer water request, solved allocation, deficit, and reach-wise status
            </div>
          </div>

          {/* Table Filters */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#263445' }}>
              Reach:
              <select
                value={filterReach}
                onChange={(e) => setFilterReach(e.target.value)}
                style={{
                  marginLeft: '4px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  border: '1px solid var(--border-default)',
                  borderRadius: '3px',
                  backgroundColor: '#FFFFFF',
                }}
              >
                <option value="all">All Reaches</option>
                <option value="Head-Reach">Head-Reach</option>
                <option value="Middle-Reach">Middle-Reach</option>
                <option value="Tail-Reach">Tail-Reach</option>
              </select>
            </label>

            <label style={{ fontSize: '12px', fontWeight: 600, color: '#263445' }}>
              Status:
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                style={{
                  marginLeft: '4px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  border: '1px solid var(--border-default)',
                  borderRadius: '3px',
                  backgroundColor: '#FFFFFF',
                }}
              >
                <option value="all">All Statuses</option>
                <option value="Adequate">Adequate</option>
                <option value="Partial">Partial</option>
                <option value="Shortage">Shortage</option>
              </select>
            </label>
          </div>
        </div>

        {/* Responsive Table */}
        <div className="table-responsive">
          <table className="gov-data-table" aria-label="Water Allocation Table">
            <thead>
              <tr>
                <th>Farmer ID</th>
                <th>Farmer Name</th>
                <th>Crop</th>
                <th style={{ textAlign: 'right' }}>Farm Area (ha)</th>
                <th style={{ textAlign: 'right' }}>Water Requested (m³)</th>
                <th style={{ textAlign: 'right' }}>Water Allocated (m³)</th>
                <th style={{ textAlign: 'right' }}>Water Deficit (m³)</th>
                <th>Canal Reach</th>
                <th style={{ textAlign: 'center' }}>Allocation Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    No records matching the selected reach or status filters.
                  </td>
                </tr>
              ) : (
                filteredRows.map((row) => (
                  <tr key={row.farmer_id}>
                    <td style={{ fontWeight: 600, color: '#12315B' }}>{row.farmer_id}</td>
                    <td style={{ fontWeight: 600 }}>{row.farmer_name}</td>
                    <td>{row.crop}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {row.area_ha.toFixed(1)}
                    </td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {formatWater(row.requested_m3)}
                    </td>
                    <td
                      style={{
                        textAlign: 'right',
                        fontWeight: 600,
                        color: '#176B45',
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {formatWater(row.allocated_m3)}
                    </td>
                    <td
                      style={{
                        textAlign: 'right',
                        fontWeight: 600,
                        color: row.deficit_m3 > 0 ? '#B42318' : 'var(--text-muted)',
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {formatWater(row.deficit_m3)}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '11px',
                          padding: '2px 6px',
                          borderRadius: '2px',
                          backgroundColor:
                            row.reach === 'Head-Reach'
                              ? '#eef3f9'
                              : row.reach === 'Middle-Reach'
                              ? '#f5f7f9'
                              : '#fef3f2',
                          color:
                            row.reach === 'Head-Reach'
                              ? '#12315B'
                              : row.reach === 'Middle-Reach'
                              ? '#4e6178'
                              : '#B42318',
                          fontWeight: 600,
                        }}
                      >
                        {row.reach}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {row.status === 'Adequate' && (
                        <span className="status-badge-adequate">
                          <CheckCircle2 size={12} />
                          Adequate
                        </span>
                      )}
                      {row.status === 'Partial' && (
                        <span className="status-badge-partial">
                          <AlertTriangle size={12} />
                          Partial
                        </span>
                      )}
                      {row.status === 'Shortage' && (
                        <span className="status-badge-shortage">
                          <AlertOctagon size={12} />
                          Shortage
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Section 3: Distribution Summary Charts (Recharts) ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))',
          gap: '20px',
          marginBottom: '24px',
        }}
      >
        {/* Chart 1: Requested vs Allocated Water */}
        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-default)',
            padding: '16px',
            borderRadius: '4px',
          }}
        >
          <div style={{ marginBottom: '12px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#12315B', margin: 0 }}>
              Requested vs Allocated Water (by Farmer)
            </h3>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Comparison of predicted crop demand vs optimized canal supply (m³)
            </div>
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={requestedVsAllocatedData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D9E0E7" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#263445', fontSize: 11 }} />
                <YAxis tick={{ fill: '#263445', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #D9E0E7',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                  formatter={(val: unknown) => [`${val} m³`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '6px' }} />
                <Bar dataKey="Requested" name="Water Requested" fill="#12315B" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Allocated" name="Water Allocated" fill="#176B45" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Crop-Wise Water Demand */}
        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-default)',
            padding: '16px',
            borderRadius: '4px',
          }}
        >
          <div style={{ marginBottom: '12px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#12315B', margin: 0 }}>
              Crop-Wise Water Demand
            </h3>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Total irrigation demand and allocation aggregated by crop type (m³)
            </div>
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={cropWiseDemandData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D9E0E7" vertical={false} />
                <XAxis dataKey="crop" tick={{ fill: '#263445', fontSize: 11 }} />
                <YAxis tick={{ fill: '#263445', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #D9E0E7',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                  formatter={(val: unknown) => [`${val} m³`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '6px' }} />
                <Bar dataKey="Demand" name="Crop Demand" fill="#C58B20" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Allocated" name="Allocated" fill="#176B45" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Reach Allocation (Head vs Middle vs Tail Reach) */}
        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-default)',
            padding: '16px',
            borderRadius: '4px',
          }}
        >
          <div style={{ marginBottom: '12px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#12315B', margin: 0 }}>
              Canal Reach Allocation Analysis
            </h3>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Head-Reach vs Middle-Reach vs Tail-Reach allocation &amp; conveyance equity (m³)
            </div>
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={reachData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D9E0E7" vertical={false} />
                <XAxis dataKey="reach" tick={{ fill: '#263445', fontSize: 11 }} />
                <YAxis tick={{ fill: '#263445', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #D9E0E7',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                  formatter={(val: unknown) => [`${val} m³`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '6px' }} />
                <Bar dataKey="Allocated" name="Allocated Water" fill="#176B45" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Deficit" name="Reach Deficit" fill="#B42318" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Water Shortage Distribution */}
        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-default)',
            padding: '16px',
            borderRadius: '4px',
          }}
        >
          <div style={{ marginBottom: '12px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#12315B', margin: 0 }}>
              Water Shortage Distribution
            </h3>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Proportion of farmers receiving Adequate, Partial, or Shortage supply
            </div>
          </div>
          <div style={{ width: '100%', height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={statusPieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  dataKey="value"
                  label={({ name, percent }: { name?: string; percent?: number }) =>
                    `${name || ''}: ${((percent || 0) * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {statusPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: unknown, name: unknown) => [`${value} Farmers`, `${name}`]}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Section 4: Formal Government Notice & Audit Footer ── */}
      <div
        style={{
          background: '#ffffff',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid #176B45',
          padding: '14px 18px',
          fontSize: '12px',
          color: 'var(--text-muted)',
          lineHeight: '1.6',
        }}
      >
        <strong style={{ color: '#12315B' }}>Administrative &amp; Scientific Notice:</strong> Water
        allocations are computed deterministically using standard FAO-56 crop evapotranspiration formulas
        and OR-Tools Linear Programming (GLOP). All figures represent simulated water demand and
        administrative distribution within the canal command area for mediation and decision support.
      </div>
    </div>
  );
};
