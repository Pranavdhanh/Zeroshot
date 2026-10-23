import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  AlertTriangle,
  Lock,
  Activity,
  Zap,
  Clock,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Search,
  ExternalLink,
  X,
  PieChart as PieIcon,
  BarChart3,
  CheckCircle,
  Server
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { fetchDashboardSummary, fetchAlerts } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useBackendStatus } from '../context/BackendStatusContext';
import { useToast } from '../context/ToastContext';
import { useNavigate } from 'react-router-dom';

export default function DashboardPage() {
  const { t } = useLanguage();
  const { isOnline } = useBackendStatus();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [sumRes, altRes] = await Promise.all([
        fetchDashboardSummary(),
        fetchAlerts()
      ]);
      setSummary(sumRes.data);
      setAlerts(altRes.data);
      setIsFallback(sumRes.isFallback || altRes.isFallback);
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Dashboard Error',
        message: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (loading && !summary) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-slate-400">Loading intelligence telemetry...</p>
      </div>
    );
  }

  const kpis = [
    {
      title: t('dash_total_vol'),
      value: summary ? `₹${(summary.total_volume_inr / 10000000).toFixed(1)} Cr` : '₹89.4 Cr',
      subtext: `${summary?.total_transactions?.toLocaleString() || '142,850'} total transactions`,
      icon: Activity,
      color: 'text-cyan-400',
      bg: 'bg-cyan-950/40',
      border: 'border-cyan-500/30'
    },
    {
      title: t('dash_flagged_warns'),
      value: summary?.flagged_transactions?.toLocaleString() || '3,420',
      subtext: 'High-risk friction prompts',
      icon: AlertTriangle,
      color: 'text-amber-400',
      bg: 'bg-amber-950/40',
      border: 'border-amber-500/30'
    },
    {
      title: t('dash_holds'),
      value: summary?.blocked_holds?.toLocaleString() || '812',
      subtext: 'Pre-debit funds prevented',
      icon: Lock,
      color: 'text-rose-400',
      bg: 'bg-rose-950/40',
      border: 'border-rose-500/30'
    },
    {
      title: t('dash_mule_intercepted'),
      value: summary?.mule_accounts_intercepted || '138',
      subtext: 'GovTech I4C network hits',
      icon: ShieldAlert,
      color: 'text-purple-400',
      bg: 'bg-purple-950/40',
      border: 'border-purple-500/30'
    },
    {
      title: t('dash_avg_latency'),
      value: `${summary?.avg_latency_ms || 11.4} ms`,
      subtext: 'Mean XGBoost inference speed',
      icon: Zap,
      color: 'text-emerald-400',
      bg: 'bg-emerald-950/40',
      border: 'border-emerald-500/30'
    }
  ];

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <LayoutDashboard className="w-5 h-5 text-accent-cyan-bright" />
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              {t('dash_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('dash_subtitle')}
          </p>
        </div>

        <button
          onClick={loadDashboardData}
          disabled={loading}
          className="self-start md:self-auto flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-surface border border-surface-border hover:border-slate-500 text-slate-200 text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Backend / Demo Data Banner */}
      {isFallback ? (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>DEMO DATA:</strong> Live backend summary endpoint <code>GET /api/dashboard/summary</code> is offline; metrics rendered from calibrated hackathon baseline dataset.
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300">
          <Server className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Streaming live metrics from FastAPI <code>GET /api/dashboard/summary</code></span>
        </div>
      )}

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className={`fintech-card rounded-2xl p-4 border ${kpi.border} flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  {kpi.title}
                </span>
                <div className={`p-1.5 rounded-lg ${kpi.bg}`}>
                  <Icon className={`w-4 h-4 ${kpi.color}`} />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-xl font-extrabold text-white font-mono">
                  {kpi.value}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                  {kpi.subtext}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Section: Hourly Trends & Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Hourly Transaction & Fraud Trend (AreaChart) - 2 columns */}
        <div className="lg:col-span-2 fintech-card rounded-3xl p-5 border border-surface-border space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-surface-border">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent-cyan-bright" />
                24-Hour Transaction Volume & Threat Interception
              </h3>
              <p className="text-[11px] text-slate-400">
                Notice late-night surge in suspicious mule pass-through attempts (02:00 - 04:00 AM)
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-navy-950 border border-surface-border text-slate-400">
              Hourly Aggregate
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary?.hourly_trends || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorSuspicious" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.6}/>
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorHolds" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="hour" stroke="#64748B" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748B" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#23324E', borderRadius: '12px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Area type="monotone" dataKey="total" stroke="#06B6D4" fillOpacity={1} fill="url(#colorTotal)" name="Total Txns" />
                <Area type="monotone" dataKey="suspicious" stroke="#F59E0B" fillOpacity={1} fill="url(#colorSuspicious)" name="Flagged Friction" />
                <Area type="monotone" dataKey="holds" stroke="#EF4444" fillOpacity={1} fill="url(#colorHolds)" name="Blocked Holds" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Score Distribution (BarChart) - 1 column */}
        <div className="fintech-card rounded-3xl p-5 border border-surface-border space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-surface-border">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              Risk Score Distribution
            </h3>
            <span className="text-[10px] font-mono text-slate-400">0 - 100 Range</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary?.risk_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="range" stroke="#64748B" tick={{ fontSize: 9 }} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748B" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#23324E', borderRadius: '12px', fontSize: '11px' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {(summary?.risk_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Threat Typology Breakdown & Recent Real-Time Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Donut Chart: Typology */}
        <div className="fintech-card rounded-3xl p-5 border border-surface-border space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 pb-2 border-b border-surface-border">
            <PieIcon className="w-4 h-4 text-purple-400" />
            Intercepted Threat Typologies
          </h3>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={summary?.typology_breakdown || []}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                >
                  {(summary?.typology_breakdown || []).map((entry, index) => (
                    <Cell key={`slice-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#23324E', borderRadius: '12px', fontSize: '11px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 pt-1">
            {(summary?.typology_breakdown || []).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-[11px] truncate max-w-[150px]">{item.name}</span>
                </div>
                <span className="font-mono text-slate-400 text-[11px]">{item.percentage}% ({item.count})</span>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Alerts Table - 2 columns */}
        <div className="lg:col-span-2 fintech-card rounded-3xl p-5 border border-surface-border space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-surface-border">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Live Anomaly Alerts (GovTech & Bank FIU Queue)
              </h3>
              <p className="text-[11px] text-slate-400">
                Click any alert row to view investigation dossier and automated mitigation
              </p>
            </div>
            <button
              onClick={() => navigate('/cases')}
              className="text-xs font-semibold text-accent-cyan-bright hover:underline flex items-center gap-1"
            >
              All Cases <ExternalLink className="w-3 h-3" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase tracking-wider text-slate-500 border-b border-surface-border">
                <tr>
                  <th className="py-2.5 px-3">Alert ID</th>
                  <th className="py-2.5 px-3">Suspect VPA</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Trigger Signature</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {alerts.map((alt) => (
                  <tr
                    key={alt.alert_id}
                    onClick={() => setSelectedAlert(alt)}
                    className="hover:bg-surface/50 cursor-pointer transition-colors group"
                  >
                    <td className="py-3 px-3 font-mono text-cyan-400 font-semibold group-hover:text-cyan-300">
                      {alt.alert_id}
                      <span className="block text-[10px] text-slate-500 font-sans">{alt.timestamp}</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-200">
                      {alt.account}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          alt.severity === 'CRITICAL'
                            ? 'bg-rose-950 text-rose-300 border border-rose-500/30'
                            : alt.severity === 'HIGH'
                            ? 'bg-amber-950 text-amber-300 border border-amber-500/30'
                            : 'bg-blue-950 text-blue-300 border border-blue-500/30'
                        }`}
                      >
                        {alt.severity} ({alt.risk_score})
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300 max-w-[220px] truncate">
                      {alt.trigger}
                    </td>
                    <td className="py-3 px-3 text-slate-400 group-hover:text-white font-medium text-[11px]">
                      {alt.status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* Alert Investigation Detail Slide-Over / Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-lg w-full fintech-card rounded-3xl p-6 border border-rose-500/30 red-glow animate-scale-up space-y-4">
            
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                <div>
                  <span className="font-bold text-white text-base">Alert Dossier: {selectedAlert.alert_id}</span>
                  <span className="text-xs text-slate-400 block font-sans">{selectedAlert.timestamp}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="p-1 rounded-lg hover:bg-surface text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-navy-950 border border-surface-border space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Suspect VPA:</span>
                <span className="font-mono text-cyan-400 font-bold">{selectedAlert.account}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Calculated Risk:</span>
                <span className="font-mono font-bold text-rose-400">{selectedAlert.risk_score} / 100 ({selectedAlert.severity})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Mitigation Taken:</span>
                <span className="text-emerald-400 font-medium">{selectedAlert.action_taken}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-navy-950 border border-surface-border text-xs space-y-1">
              <span className="font-semibold text-slate-300 block">Trigger Telemetry Signature:</span>
              <p className="text-slate-300 leading-relaxed">{selectedAlert.trigger}</p>
            </div>

            <div className="flex gap-2.5 pt-2">
              <button
                onClick={() => {
                  setSelectedAlert(null);
                  navigate('/network');
                }}
                className="flex-1 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-navy-950 font-bold text-xs transition-colors"
              >
                Trace in Mule Network Graph
              </button>
              <button
                onClick={() => {
                  setSelectedAlert(null);
                  navigate('/cases');
                }}
                className="px-4 py-2.5 rounded-xl bg-surface border border-surface-border hover:border-slate-500 text-xs font-semibold text-slate-200"
              >
                View Case File
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
