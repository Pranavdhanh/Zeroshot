import React from 'react';
import {
  ShieldAlert,
  Lock,
  RotateCcw,
  GitFork,
  ExternalLink,
  PhoneCall,
  CheckCircle2,
  AlertOctagon,
  FileText
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import FraudDecisionComponent from './FraudDecisionComponent';

export default function HoldDecisionScreen({ decisionData, onReset }) {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { addToast } = useToast();

  if (!decisionData) return null;

  const handleCyberReport = () => {
    addToast({
      type: 'success',
      title: 'Report Dossier Queued',
      message: 'Suspicious VPA has been packaged for National Cyber Crime Portal (1930 / I4C) investigation.'
    });
    navigate('/cases');
  };

  return (
    <div className="max-w-xl mx-auto space-y-4 animate-fade-in">
      
      {/* Critical Hold Alert Header */}
      <div className="p-5 rounded-2xl bg-rose-950/50 border border-rose-500/50 flex items-start gap-4 red-glow">
        <div className="w-12 h-12 rounded-xl bg-rose-900/70 border border-rose-500/40 flex items-center justify-center shrink-0">
          <AlertOctagon className="w-7 h-7 text-rose-400 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-rose-300">
              {t('outcome_hold_title')}
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-900 text-rose-200 border border-rose-500/40">
              BLOCKED
            </span>
          </div>
          <p className="text-xs text-rose-200/90 mt-1.5 leading-relaxed">
            {t('outcome_hold_msg')}
          </p>
        </div>
      </div>

      {/* Reassurance Notice - NO MONEY DEDUCTED */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-700/80 flex items-center gap-3">
        <Lock className="w-5 h-5 text-emerald-400 shrink-0" />
        <div className="text-xs text-slate-300">
          <span className="font-semibold text-white">Your Bank Funds Are 100% Safe: </span>
          <span>Payment was halted prior to NPCI debit switch. No money was transferred.</span>
        </div>
      </div>

      {/* Embedded Fraud Decision Card with Reasons in English & Tamil */}
      <FraudDecisionComponent decisionData={decisionData} />

      {/* Interception Intelligence Summary */}
      <div className="p-4 rounded-xl bg-surface border border-surface-border text-xs space-y-2.5">
        <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>Interception Metadata</span>
        </h4>
        <div className="grid grid-cols-2 gap-3 text-slate-300 pt-1">
          <div>
            <span className="text-slate-500 text-[11px] block">Blocked VPA</span>
            <span className="font-mono text-cyan-400 font-medium">{decisionData.recipient_upi}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Attempted Amount</span>
            <span className="font-bold text-white">₹{Number(decisionData.amount).toLocaleString('en-IN')}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Recommended Action</span>
            <span className="text-rose-400 font-medium">Lien & Suspend VPA</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">GovTech Escalation</span>
            <span className="text-amber-400 font-medium">I4C Mule Registry Sync</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <button
          onClick={onReset}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-surface border border-surface-border hover:bg-surface-hover hover:border-slate-500 text-slate-200 text-xs font-semibold transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          <span>{t('btn_make_another')}</span>
        </button>

        <button
          onClick={() => navigate('/network')}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-surface border border-surface-border hover:border-cyan-500/40 text-cyan-400 text-xs font-semibold transition-colors"
          title="Inspect account in Mule Network"
        >
          <GitFork className="w-4 h-4" />
          <span>{t('btn_view_network')}</span>
        </button>

        <button
          onClick={handleCyberReport}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-colors shadow-lg shadow-rose-600/30"
        >
          <PhoneCall className="w-4 h-4" />
          <span>{t('btn_report_cyber')}</span>
        </button>
      </div>

    </div>
  );
}
