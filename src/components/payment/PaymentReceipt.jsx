import React from 'react';
import {
  CheckCircle,
  Share2,
  Download,
  RotateCcw,
  ShieldCheck,
  ExternalLink,
  Building,
  CreditCard,
  Hash
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';

export default function PaymentReceipt({ transaction, onReset }) {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { addToast } = useToast();

  if (!transaction) return null;

  const {
    recipient_name,
    recipient_upi,
    amount,
    sender_name,
    sender_bank = 'HDFC Bank',
    sender_account = '•••• 4821',
    note,
    utr = `4291${Math.floor(10000000 + Math.random() * 90000000)}`,
    transaction_id,
    risk_score,
    latency_ms,
    timestamp = new Date().toISOString()
  } = transaction;

  const formattedDate = new Date(timestamp).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'medium'
  });

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(
        `UPI Shield AI Receipt\nUTR: ${utr}\nAmount: ₹${Number(amount).toLocaleString('en-IN')}\nTo: ${recipient_name} (${recipient_upi})\nStatus: Successful`
      );
      addToast({
        type: 'success',
        title: 'Receipt Copied',
        message: 'Transaction reference copied to clipboard.'
      });
    }
  };

  return (
    <div className="max-w-md mx-auto fintech-card rounded-3xl p-6 border border-emerald-500/30 green-glow animate-fade-in relative overflow-hidden">
      
      {/* Decorative background watermark */}
      <div className="absolute -top-12 -right-12 w-40 h-40 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

      {/* Success Badge */}
      <div className="flex flex-col items-center text-center pb-6 border-b border-surface-border">
        <div className="w-16 h-16 rounded-full bg-emerald-950 border-2 border-emerald-400 flex items-center justify-center mb-3 shadow-lg shadow-emerald-500/20">
          <CheckCircle className="w-10 h-10 text-emerald-400" />
        </div>
        <span className="text-[11px] font-semibold tracking-widest uppercase text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
          {t('receipt_status_success')}
        </span>
        <div className="text-3xl font-extrabold text-white mt-3 font-sans">
          ₹ {Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Paid to <span className="font-semibold text-slate-200">{recipient_name}</span>
        </p>
        <span className="text-xs font-mono text-cyan-400 mt-0.5">
          {recipient_upi}
        </span>
      </div>

      {/* Transaction Details Table */}
      <div className="py-4 space-y-3 text-xs border-b border-surface-border font-sans">
        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">{t('receipt_utr')}</span>
          <span className="font-mono font-medium text-slate-100">{utr}</span>
        </div>

        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">{t('receipt_tx_id')}</span>
          <span className="font-mono font-medium text-accent-cyan-bright">{transaction_id}</span>
        </div>

        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">{t('receipt_date')}</span>
          <span className="text-slate-200">{formattedDate}</span>
        </div>

        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">Debited From</span>
          <span className="text-slate-200 flex items-center gap-1.5">
            <Building className="w-3.5 h-3.5 text-slate-400" />
            {sender_bank} ({sender_account})
          </span>
        </div>

        {note && (
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Note</span>
            <span className="text-slate-200 italic">"{note}"</span>
          </div>
        )}

        <div className="flex justify-between items-center text-slate-300">
          <span className="text-slate-400">Risk Assessment</span>
          <span className="inline-flex items-center gap-1 font-semibold text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            Score: {risk_score}/100 ({latency_ms}ms)
          </span>
        </div>
      </div>

      {/* Academic simulation disclaimer */}
      <div className="pt-3 pb-4 text-center">
        <p className="text-[10px] text-slate-500">
          Protected by UPI Shield AI Real-Time ML Engine • Track 4 FinTech Intelligence
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-2.5 pt-2">
        <button
          onClick={onReset}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-accent-cyan hover:bg-accent-cyan-bright text-navy-950 font-semibold text-xs transition-colors shadow-lg shadow-cyan-500/20"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>{t('btn_make_another')}</span>
        </button>
        <button
          onClick={handleShare}
          className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-surface border border-surface-border hover:border-slate-500 text-slate-200 text-xs transition-colors"
          title="Copy receipt details"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>Share</span>
        </button>
        <button
          onClick={() => navigate('/transactions')}
          className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-surface border border-surface-border hover:border-slate-500 text-slate-200 text-xs transition-colors"
          title="View in Transactions Audit"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          <span>Feed</span>
        </button>
      </div>

    </div>
  );
}
