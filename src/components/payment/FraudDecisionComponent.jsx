import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Cpu,
  AlertCircle,
  HelpCircle,
  Server
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export default function FraudDecisionComponent({ decisionData }) {
  const { lang, t, translateReason } = useLanguage();

  if (!decisionData) return null;

  const {
    risk_score = 0,
    decision = 'WARN',
    reasons = [],
    latency_ms = 0,
    isFallback = false,
    source = 'LIVE_BACKEND_FASTAPI'
  } = decisionData;

  // Determine styling based on decision
  const isAllow = decision === 'ALLOW';
  const isWarn = decision === 'WARN';
  const isHold = decision === 'HOLD';

  const badgeConfig = isAllow
    ? {
        border: 'border-emerald-500/40',
        bg: 'bg-emerald-950/40',
        text: 'text-emerald-400',
        indicator: 'bg-emerald-500',
        glow: 'green-glow',
        title: t('outcome_allow_title'),
        desc: t('outcome_allow_msg'),
        icon: ShieldCheck,
      }
    : isWarn
    ? {
        border: 'border-amber-500/40',
        bg: 'bg-amber-950/40',
        text: 'text-amber-400',
        indicator: 'bg-amber-500',
        glow: 'amber-glow',
        title: t('outcome_warn_title'),
        desc: t('outcome_warn_msg'),
        icon: AlertTriangle,
      }
    : {
        border: 'border-rose-500/40',
        bg: 'bg-rose-950/40',
        text: 'text-rose-400',
        indicator: 'bg-rose-500',
        glow: 'red-glow',
        title: t('outcome_hold_title'),
        desc: t('outcome_hold_msg'),
        icon: ShieldAlert,
      };

  const Icon = badgeConfig.icon;

  return (
    <div className={`p-5 rounded-2xl border ${badgeConfig.border} ${badgeConfig.bg} backdrop-blur-md transition-all ${badgeConfig.glow}`}>
      
      {/* Backend Source & Fallback Transparency Banner */}
      <div className="mb-4">
        {isFallback ? (
          <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-amber-950/60 border border-amber-500/30 text-amber-200 text-xs">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold tracking-wide uppercase text-[11px] text-amber-300">
                {t('fallback_badge')}
              </span>
              <p className="text-[11px] text-amber-200/80 mt-0.5">
                {t('fallback_expl')}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs">
            <div className="flex items-center gap-2">
              <Server className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-semibold text-[11px] tracking-wide">
                FASTAPI ML ENGINE: LIVE VERDICT
              </span>
            </div>
            <span className="font-mono text-[10px] text-emerald-400/90">
              POST /api/transactions/score
            </span>
          </div>
        )}
      </div>

      {/* Decision Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${badgeConfig.bg} border ${badgeConfig.border}`}>
            <Icon className={`w-6 h-6 ${badgeConfig.text}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xl font-bold tracking-tight ${badgeConfig.text}`}>
                {decision}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                ({t(`decision_${decision.toLowerCase()}`)})
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              {badgeConfig.title}
            </p>
          </div>
        </div>

        {/* Score & Latency Badges */}
        <div className="flex items-center gap-3">
          {/* Latency badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-surface-border text-xs font-mono text-slate-300">
            <Clock className="w-3.5 h-3.5 text-accent-cyan-bright" />
            <span>{latency_ms} ms</span>
          </div>

          {/* Risk Score Gauge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-surface-border">
            <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase tracking-wider text-slate-400">
                {t('risk_score')}
              </span>
              <span className={`text-base font-bold font-mono ${badgeConfig.text}`}>
                {risk_score} / 100
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Risk Progress Bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5 font-medium">
          <span>0 (Safe)</span>
          <span className="text-amber-400">35 (Warn Threshold)</span>
          <span className="text-rose-400">70 (Hold Threshold)</span>
          <span>100 (Critical)</span>
        </div>
        <div className="w-full h-2.5 rounded-full bg-slate-900 border border-slate-700/60 overflow-hidden relative">
          <div
            className={`h-full transition-all duration-700 ease-out rounded-full ${
              isAllow ? 'bg-emerald-500' : isWarn ? 'bg-amber-500' : 'bg-rose-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(5, risk_score))}%` }}
          />
        </div>
      </div>

      {/* AI Reasons & Explanation (English + Tamil) */}
      <div className="mt-5 space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-accent-cyan-bright" />
          <span>{t('detected_reasons')}</span>
        </h4>

        {reasons.length > 0 ? (
          <ul className="space-y-2">
            {reasons.map((reason, idx) => (
              <li
                key={idx}
                className="flex flex-col p-2.5 rounded-lg bg-navy-950/60 border border-surface-border text-xs text-slate-200"
              >
                <div className="flex items-start gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${badgeConfig.indicator}`} />
                  <span className="font-medium text-slate-100">{reason}</span>
                </div>
                {/* Tamil Translation subtitle if language is Tamil or to aid bilingual comprehension */}
                {lang === 'ta' && (
                  <span className="text-[11px] text-accent-cyan-bright mt-1 pl-3.5 font-sans">
                    {translateReason(reason)}
                  </span>
                )}
                {lang === 'en' && translateReason(reason) !== reason && (
                  <span className="text-[10px] text-slate-400 mt-0.5 pl-3.5 italic">
                    தமிழ்: {translateReason(reason)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-2.5 rounded-lg bg-navy-950/40 border border-surface-border text-xs text-slate-400">
            No specific anomalies flagged by inference pipeline.
          </div>
        )}
      </div>

    </div>
  );
}
