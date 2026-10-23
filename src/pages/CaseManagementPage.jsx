import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Search,
  Filter,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  Users,
  IndianRupee,
  FileText,
  Save,
  X,
  ExternalLink,
  ChevronRight,
  Server,
  AlertCircle
} from 'lucide-react';
import { fetchCases, updateCaseStatus } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useToast } from '../context/ToastContext';

export default function CaseManagementPage() {
  const { t } = useLanguage();
  const { addToast } = useToast();

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCase, setSelectedCase] = useState(null);
  const [newAnalystNote, setNewAnalystNote] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const loadCases = async () => {
    setLoading(true);
    try {
      const res = await fetchCases();
      setIsFallback(res.isFallback);
      setCases(res.data || []);
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Error Loading Cases',
        message: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleStatusChange = async (caseId, newStatus) => {
    setUpdatingStatus(true);
    try {
      const res = await updateCaseStatus(caseId, newStatus, newAnalystNote);
      
      // Update local cases state
      setCases((prev) =>
        prev.map((c) =>
          c.case_id === caseId
            ? {
                ...c,
                status: newStatus,
                evidence: newAnalystNote
                  ? [...c.evidence, `[Analyst Note]: ${newAnalystNote}`]
                  : c.evidence
              }
            : c
        )
      );

      if (selectedCase && selectedCase.case_id === caseId) {
        setSelectedCase((prev) => ({
          ...prev,
          status: newStatus,
          evidence: newAnalystNote
            ? [...prev.evidence, `[Analyst Note]: ${newAnalystNote}`]
            : prev.evidence
        }));
      }

      setNewAnalystNote('');

      if (!res.isFallback) {
        addToast({
          type: 'success',
          title: 'Case Updated (Live)',
          message: `Backend PATCH /api/cases/${caseId} confirmed status '${newStatus}'.`
        });
      } else {
        addToast({
          type: 'info',
          title: 'Status Updated (Local Sandbox)',
          message: `Backend PATCH endpoint offline. Saved locally as '${newStatus}'.`
        });
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: err.message
      });
    } finally {
      setUpdatingStatus(false);
    }
  };

  const filteredCases = cases.filter((c) => {
    if (statusFilter !== 'ALL' && c.status !== statusFilter) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.case_id.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      c.suspect_upi.toLowerCase().includes(q) ||
      c.suspect_name.toLowerCase().includes(q)
    );
  });

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-accent-cyan-bright" />
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              {t('case_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('case_subtitle')}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="px-3 py-1.5 rounded-xl bg-surface border border-surface-border">
            Total Dossiers: <strong className="text-white">{cases.length}</strong>
          </span>
        </div>
      </div>

      {/* Backend Status Notice */}
      {isFallback ? (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>DEMO DATA:</strong> Backend <code>GET /api/cases</code> is offline. Displaying local GovTech investigation dossiers. Status changes are stored in local session.
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300">
          <Server className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Syncing with live GovTech backend: <code>GET /api/cases</code></span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="fintech-card rounded-2xl p-4 border border-surface-border flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Case ID, VPA, suspect, or title..."
            className="w-full bg-navy-950 border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-navy-950 p-1 rounded-xl border border-surface-border text-xs shrink-0">
          {['ALL', 'OPEN', 'INVESTIGATING', 'CLOSED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                statusFilter === st
                  ? 'bg-surface-elevated text-accent-cyan-bright border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st === 'ALL' ? t('case_filter_all') : st}
            </button>
          ))}
        </div>
      </div>

      {/* Cases List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs">Loading investigation dossiers...</p>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2 fintech-card rounded-3xl border border-surface-border">
            <Briefcase className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">No cases found</p>
            <p className="text-xs text-slate-500">Try adjusting your search or status filter.</p>
          </div>
        ) : (
          filteredCases.map((c) => {
            const isCritical = c.priority === 'CRITICAL';
            const isHigh = c.priority === 'HIGH';
            const isOpen = c.status === 'OPEN';
            const isInvestigating = c.status === 'INVESTIGATING';
            const isClosed = c.status === 'CLOSED';

            return (
              <div
                key={c.case_id}
                onClick={() => setSelectedCase(c)}
                className="fintech-card rounded-2xl p-5 border border-surface-border hover:border-slate-500 transition-all cursor-pointer group flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-cyan-400 font-bold text-xs">
                      {c.case_id}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        isCritical
                          ? 'bg-rose-950 text-rose-300 border border-rose-500/30'
                          : isHigh
                          ? 'bg-amber-950 text-amber-300 border border-amber-500/30'
                          : 'bg-blue-950 text-blue-300 border border-blue-500/30'
                      }`}
                    >
                      {c.priority} PRIORITY
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                        isOpen
                          ? 'bg-amber-950 text-amber-300'
                          : isInvestigating
                          ? 'bg-cyan-950 text-cyan-300'
                          : 'bg-emerald-950 text-emerald-300'
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white group-hover:text-accent-cyan-bright transition-colors font-sans">
                    {c.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-1">
                    {c.summary}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 pt-1">
                    <span className="font-mono text-slate-300">Suspect: {c.suspect_upi}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-slate-500" />
                      {c.victims_count} Reported Victims
                    </span>
                    <span>•</span>
                    <span className="text-white font-semibold">{c.amount_at_risk} at Risk</span>
                    <span>•</span>
                    <span className="text-slate-500">{c.created_at}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCase(c);
                    }}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-surface border border-surface-border group-hover:border-cyan-500/40 text-xs font-semibold text-slate-200 transition-colors"
                  >
                    <span>Dossier</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Detailed Case File Modal */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-2xl w-full fintech-card rounded-3xl p-6 sm:p-7 border border-surface-border cyan-glow animate-scale-up space-y-5 max-h-[90vh] overflow-y-auto">
            
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-surface-border">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-cyan-400 text-xs">
                    {selectedCase.case_id}
                  </span>
                  <span className="text-xs text-slate-500">|</span>
                  <span className="text-xs font-semibold text-amber-400">
                    {selectedCase.typology}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">
                  {selectedCase.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="p-1 rounded-lg hover:bg-surface text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Case Key Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border">
                <span className="text-slate-500 text-[10px] uppercase block">Current Status</span>
                <span className="font-bold text-cyan-300 mt-0.5 block">{selectedCase.status}</span>
              </div>
              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border">
                <span className="text-slate-500 text-[10px] uppercase block">Victims Affected</span>
                <span className="font-bold text-white mt-0.5 block">{selectedCase.victims_count} Accounts</span>
              </div>
              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border">
                <span className="text-slate-500 text-[10px] uppercase block">Capital at Risk</span>
                <span className="font-bold text-emerald-400 mt-0.5 block">{selectedCase.amount_at_risk}</span>
              </div>
              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border">
                <span className="text-slate-500 text-[10px] uppercase block">Assigned Unit</span>
                <span className="font-semibold text-slate-300 mt-0.5 block truncate">{selectedCase.assigned_analyst}</span>
              </div>
            </div>

            {/* Suspect Profile */}
            <div className="p-3.5 rounded-xl bg-navy-950 border border-surface-border text-xs space-y-1.5">
              <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">
                Suspect Target Entity:
              </span>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-slate-200">
                <div>
                  <span className="font-bold text-white">{selectedCase.suspect_name}</span>
                  <span className="font-mono text-cyan-400 ml-2">({selectedCase.suspect_upi})</span>
                </div>
                <span className="text-amber-400 text-[11px] font-medium">{selectedCase.bank_actions}</span>
              </div>
            </div>

            {/* Evidence & Forensic Findings */}
            <div className="space-y-2">
              <span className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-accent-cyan-bright" />
                Forensic Evidence Log & Traces:
              </span>
              <ul className="space-y-1.5">
                {selectedCase.evidence.map((item, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded-xl bg-navy-950/80 border border-surface-border text-xs text-slate-300 leading-relaxed"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Add Analyst Investigation Note */}
            <div className="space-y-2 pt-2 border-t border-surface-border">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block">
                {t('case_add_note')}
              </label>
              <textarea
                rows={2}
                value={newAnalystNote}
                onChange={(e) => setNewAnalystNote(e.target.value)}
                placeholder="Enter findings, NPCI case docket number, or freezing order reference..."
                className="w-full bg-navy-950 border border-surface-border rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Status Change Controls */}
            <div className="pt-3 border-t border-surface-border flex flex-col sm:flex-row items-center justify-between gap-3">
              <span className="text-xs text-slate-400">
                Update Status ({isFallback ? 'Sandbox Demo Mode' : 'FastAPI Connected'}):
              </span>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={updatingStatus || selectedCase.status === 'OPEN'}
                  onClick={() => handleStatusChange(selectedCase.case_id, 'OPEN')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface border border-surface-border hover:border-amber-400 text-amber-300 disabled:opacity-50"
                >
                  Mark Open
                </button>
                <button
                  type="button"
                  disabled={updatingStatus || selectedCase.status === 'INVESTIGATING'}
                  onClick={() => handleStatusChange(selectedCase.case_id, 'INVESTIGATING')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface border border-surface-border hover:border-cyan-400 text-cyan-300 disabled:opacity-50"
                >
                  Investigating
                </button>
                <button
                  type="button"
                  disabled={updatingStatus || selectedCase.status === 'CLOSED'}
                  onClick={() => handleStatusChange(selectedCase.case_id, 'CLOSED')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-950 border border-emerald-500/40 text-emerald-300 disabled:opacity-50"
                >
                  Close Case
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
