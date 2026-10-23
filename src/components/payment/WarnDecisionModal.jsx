import React, { useState } from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  XCircle,
  CheckSquare,
  Square,
  Clock,
  Info
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import FraudDecisionComponent from './FraudDecisionComponent';

export default function WarnDecisionModal({ decisionData, onProceed, onCancel }) {
  const { t } = useLanguage();
  const [acknowledged, setAcknowledged] = useState(false);

  if (!decisionData) return null;

  return (
    <div className="max-w-xl mx-auto space-y-4 animate-fade-in">
      
      {/* Header alert banner */}
      <div className="p-4 rounded-2xl bg-amber-950/40 border border-amber-500/40 flex items-start gap-3.5 amber-glow">
        <div className="w-10 h-10 rounded-xl bg-amber-900/60 border border-amber-500/30 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
        </div>
        <div>
          <h3 className="text-base font-bold text-amber-300">
            {t('outcome_warn_title')}
          </h3>
          <p className="text-xs text-amber-200/80 mt-1">
            {t('outcome_warn_msg')}
          </p>
        </div>
      </div>

      {/* Embedded Fraud Decision Card with Reasons in English & Tamil */}
      <FraudDecisionComponent decisionData={decisionData} />

      {/* Recipient summary recap */}
      <div className="p-4 rounded-xl bg-surface border border-surface-border text-xs space-y-2">
        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">Target Beneficiary</span>
          <span className="font-semibold text-slate-100">{decisionData.recipient_name}</span>
        </div>
        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">Target VPA</span>
          <span className="font-mono text-cyan-400">{decisionData.recipient_upi}</span>
        </div>
        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">Pending Amount</span>
          <span className="font-bold text-base text-white">
            ₹{Number(decisionData.amount).toLocaleString('en-IN')}
          </span>
        </div>
      </div>

      {/* Explicit User Acknowledgment Checkbox */}
      <div
        onClick={() => setAcknowledged(!acknowledged)}
        className="flex items-start gap-3 p-3.5 rounded-xl bg-navy-950/80 border border-amber-500/30 cursor-pointer hover:border-amber-400/50 transition-colors select-none"
      >
        <button
          type="button"
          className="mt-0.5 text-amber-400 focus:outline-none"
          aria-label="Toggle acknowledgment"
        >
          {acknowledged ? (
            <CheckSquare className="w-5 h-5 text-amber-400" />
          ) : (
            <Square className="w-5 h-5 text-slate-500" />
          )}
        </button>
        <div className="text-xs text-slate-200">
          <span className="font-semibold text-amber-300">
            Mandatory Risk Acknowledgment:
          </span>
          <p className="text-slate-400 mt-0.5">
            I confirm that I have verified the recipient's identity independently. I understand that if this is a scam, UPI transfers cannot be reversed.
          </p>
        </div>
      </div>

      {/* Action Decision Choice */}
      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <button
          onClick={onCancel}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-surface border border-surface-border hover:bg-surface-hover hover:border-slate-500 text-slate-200 text-xs font-semibold transition-colors"
        >
          <XCircle className="w-4 h-4 text-slate-400" />
          <span>{t('btn_cancel_tx')}</span>
        </button>

        <button
          onClick={onProceed}
          disabled={!acknowledged}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-semibold text-xs transition-all ${
            acknowledged
              ? 'bg-amber-500 hover:bg-amber-400 text-navy-950 shadow-lg shadow-amber-500/20 cursor-pointer'
              : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-60'
          }`}
        >
          <span>{t('btn_proceed_anyway')}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

    </div>
  );
}
