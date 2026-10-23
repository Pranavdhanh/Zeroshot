import React, { useState, useEffect, useMemo } from 'react';
import {
  History,
  Search,
  Filter,
  Download,
  AlertCircle,
  ShieldCheck,
  AlertTriangle,
  ShieldAlert,
  Clock,
  ArrowUpRight,
  ExternalLink,
  X,
  FileSpreadsheet,
  RefreshCw,
  Server
} from 'lucide-react';
import { fetchTransactions } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useBackendStatus } from '../context/BackendStatusContext';
import { useToast } from '../context/ToastContext';

export default function TransactionsPage({ localTransactions = [] }) {
  const { t, translateReason } = useLanguage();
  const { isOnline } = useBackendStatus();
  const { addToast } = useToast();

  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFallback, setIsFallback] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [selectedTx, setSelectedTx] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTransactions();
      setIsFallback(res.isFallback);
      
      // Merge with any local transactions simulated in the current session
      const backendOrMock = res.data || [];
      const combined = [...localTransactions, ...backendOrMock];
      
      // Deduplicate by transaction_id
      const unique = Array.from(new Map(combined.map(item => [item.transaction_id, item])).values());
      setTransactions(unique);
    } catch (err) {
      setError(err.message || 'Failed to fetch transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [localTransactions]);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      // Decision filter
      if (decisionFilter !== 'ALL' && tx.decision !== decisionFilter) {
        return false;
      }
      // Search query
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const idMatch = tx.transaction_id?.toLowerCase().includes(q);
      const senderMatch = tx.sender_name?.toLowerCase().includes(q) || tx.sender_upi?.toLowerCase().includes(q);
      const recipientMatch = tx.recipient_name?.toLowerCase().includes(q) || tx.recipient_upi?.toLowerCase().includes(q);
      const utrMatch = tx.utr?.toLowerCase().includes(q);
      return idMatch || senderMatch || recipientMatch || utrMatch;
    });
  }, [transactions, decisionFilter, searchQuery]);

  const handleExportCSV = () => {
    if (filteredTransactions.length === 0) {
      addToast({ type: 'warning', title: 'Export Failed', message: 'No records to export.' });
      return;
    }

    const headers = ['Transaction ID', 'UTR', 'Sender', 'Recipient', 'Amount (INR)', 'Risk Score', 'Decision', 'Timestamp', 'Reasons'];
    const rows = filteredTransactions.map((tx) => [
      tx.transaction_id,
      tx.utr || 'N/A',
      `"${tx.sender_name || tx.sender_id} (${tx.sender_upi || ''})"`,
      `"${tx.recipient_name || tx.recipient_id} (${tx.recipient_upi || ''})"`,
      tx.amount,
      tx.risk_score,
      tx.decision,
      tx.timestamp,
      `"${(tx.reasons || []).join('; ')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `UPI_Shield_Transactions_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    addToast({
      type: 'success',
      title: 'CSV Exported',
      message: `Downloaded ${filteredTransactions.length} transaction records.`
    });
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-accent-cyan-bright" />
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              {t('history_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('history_subtitle')}
          </p>
        </div>

        {/* Action controls: Refresh & Export */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface border border-surface-border hover:border-slate-500 text-slate-200 text-xs font-medium transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-accent-cyan hover:bg-accent-cyan-bright text-navy-950 text-xs font-semibold transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{t('history_export_csv')}</span>
          </button>
        </div>
      </div>

      {/* Backend Status Notice */}
      {isFallback ? (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>DEMO DATA:</strong> FastAPI endpoint <code>GET /api/transactions</code> is not running; displaying sample audit logs & session transfers.
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300">
          <Server className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Connected to live backend stream: <code>GET /api/transactions</code></span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="fintech-card rounded-2xl p-4 border border-surface-border flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('history_search_placeholder')}
            className="w-full bg-navy-950 border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Decision Category Filter Chips */}
        <div className="flex items-center gap-1.5 bg-navy-950 p-1 rounded-xl border border-surface-border text-xs shrink-0">
          {['ALL', 'ALLOW', 'WARN', 'HOLD'].map((d) => {
            const isSelected = decisionFilter === d;
            return (
              <button
                key={d}
                onClick={() => setDecisionFilter(d)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  isSelected
                    ? d === 'ALLOW'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40 shadow-sm'
                      : d === 'WARN'
                      ? 'bg-amber-950 text-amber-300 border border-amber-500/40 shadow-sm'
                      : d === 'HOLD'
                      ? 'bg-rose-950 text-rose-300 border border-rose-500/40 shadow-sm'
                      : 'bg-surface-elevated text-white border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {d === 'ALL' ? t('history_filter_all') : d}
              </button>
            );
          })}
        </div>
      </div>

      {/* Transactions Table / List */}
      <div className="fintech-card rounded-3xl border border-surface-border overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs">Fetching transactions from telemetry pipeline...</p>
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <History className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">No transactions found</p>
            <p className="text-xs text-slate-500">{t('history_empty')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-950/80 border-b border-surface-border text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Tx ID / UTR</th>
                  <th className="py-3 px-4">Sender</th>
                  <th className="py-3 px-4">Recipient</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Risk Score</th>
                  <th className="py-3 px-4">Decision</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {filteredTransactions.map((tx) => {
                  const isAllow = tx.decision === 'ALLOW';
                  const isWarn = tx.decision === 'WARN';
                  const isHold = tx.decision === 'HOLD';

                  return (
                    <tr
                      key={tx.transaction_id}
                      onClick={() => setSelectedTx(tx)}
                      className="hover:bg-surface/50 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-mono font-semibold text-slate-200 group-hover:text-cyan-400 transition-colors">
                          {tx.transaction_id}
                        </div>
                        {tx.utr && (
                          <div className="text-[10px] font-mono text-slate-500">
                            UTR: {tx.utr}
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-200">
                          {tx.sender_name || tx.sender_id}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400 truncate max-w-[130px]">
                          {tx.sender_upi || tx.sender_id}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-200">
                          {tx.recipient_name || tx.recipient_id}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400 truncate max-w-[130px]">
                          {tx.recipient_upi || tx.recipient_id}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-bold text-white font-mono text-sm">
                          ₹{Number(tx.amount).toLocaleString('en-IN')}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono font-bold ${
                              isAllow ? 'text-emerald-400' : isWarn ? 'text-amber-400' : 'text-rose-400'
                            }`}
                          >
                            {tx.risk_score}
                          </span>
                          <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className={`h-full ${
                                isAllow ? 'bg-emerald-500' : isWarn ? 'bg-amber-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${tx.risk_score}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                            isAllow
                              ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30'
                              : isWarn
                              ? 'bg-amber-950/80 text-amber-300 border border-amber-500/30'
                              : 'bg-rose-950/80 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {isAllow && <ShieldCheck className="w-3 h-3" />}
                          {isWarn && <AlertTriangle className="w-3 h-3" />}
                          {isHold && <ShieldAlert className="w-3 h-3" />}
                          {tx.decision}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                        {new Date(tx.timestamp).toLocaleString('en-IN', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <span className="text-slate-400 group-hover:text-cyan-400 text-xs font-semibold inline-flex items-center gap-1">
                          Inspect <ArrowUpRight className="w-3.5 h-3.5" />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Transaction Detail Slide-Over Modal */}
      {selectedTx && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-lg w-full fintech-card rounded-3xl p-6 border border-surface-border cyan-glow animate-scale-up space-y-4">
            
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-base">Transaction Audit Record</span>
                <span className="text-xs font-mono text-cyan-400">{selectedTx.transaction_id}</span>
              </div>
              <button
                onClick={() => setSelectedTx(null)}
                className="p-1 rounded-lg hover:bg-surface text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border">
                <span className="text-slate-400 block text-[11px]">Sender</span>
                <span className="font-semibold text-white">{selectedTx.sender_name || selectedTx.sender_id}</span>
                <span className="font-mono text-cyan-400 text-[10px] block mt-0.5">{selectedTx.sender_upi}</span>
              </div>

              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border">
                <span className="text-slate-400 block text-[11px]">Recipient</span>
                <span className="font-semibold text-white">{selectedTx.recipient_name || selectedTx.recipient_id}</span>
                <span className="font-mono text-cyan-400 text-[10px] block mt-0.5">{selectedTx.recipient_upi}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-navy-950 border border-surface-border space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Evaluated Amount:</span>
                <span className="font-bold text-base text-white">₹{Number(selectedTx.amount).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Risk Score:</span>
                <span className="font-bold font-mono text-amber-400">{selectedTx.risk_score} / 100</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Shield Verdict:</span>
                <span className="font-bold uppercase tracking-wider text-slate-200">{selectedTx.decision}</span>
              </div>
              {selectedTx.latency_ms && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Inference Latency:</span>
                  <span className="font-mono text-cyan-400">{selectedTx.latency_ms} ms</span>
                </div>
              )}
            </div>

            {/* Reasons */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Evaluation Factors & Reasons:
              </h4>
              <ul className="space-y-1.5">
                {(selectedTx.reasons || ['Standard profile evaluation']).map((r, i) => (
                  <li key={i} className="text-xs p-2 rounded-lg bg-navy-950 border border-surface-border text-slate-200">
                    <div>{r}</div>
                    {translateReason(r) !== r && (
                      <div className="text-[10px] text-accent-cyan-bright mt-0.5 italic">
                        தமிழ்: {translateReason(r)}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedTx(null)}
                className="px-4 py-2 rounded-xl bg-surface border border-surface-border hover:bg-surface-hover text-xs font-semibold text-slate-200"
              >
                Close Audit Record
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
