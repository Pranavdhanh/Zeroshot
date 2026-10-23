import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Layers,
  Activity,
  RotateCcw,
  AlertTriangle
} from 'lucide-react';
import PaymentForm from '../components/payment/PaymentForm';
import PaymentReceipt from '../components/payment/PaymentReceipt';
import WarnDecisionModal from '../components/payment/WarnDecisionModal';
import HoldDecisionScreen from '../components/payment/HoldDecisionScreen';
import { scoreTransaction } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useToast } from '../context/ToastContext';

export default function PaymentSimulatorPage({ onAddTransaction }) {
  const { t } = useLanguage();
  const { addToast } = useToast();

  // State: 'FORM' | 'ANALYZING' | 'ALLOW_RECEIPT' | 'WARN_CONFIRMATION' | 'HOLD_BLOCKED'
  const [currentStep, setCurrentStep] = useState('FORM');
  const [stageIndex, setStageIndex] = useState(0);
  const [currentTransaction, setCurrentTransaction] = useState(null);
  const [decisionResult, setDecisionResult] = useState(null);

  const stages = [
    t('stage_fingerprint'),
    t('stage_velocity'),
    t('stage_mule_check'),
    t('stage_ml_eval')
  ];

  const handleStartAnalysis = async (payload) => {
    setCurrentTransaction(payload);
    setCurrentStep('ANALYZING');
    setStageIndex(0);

    // Realistic ML pipeline stage progression for hackathon visual impact
    const stepInterval = setInterval(() => {
      setStageIndex((prev) => {
        if (prev < stages.length - 1) return prev + 1;
        return prev;
      });
    }, 450);

    try {
      // Execute scoring API call to backend (or deterministic fallback if backend offline)
      const result = await scoreTransaction(payload);

      // Keep animation clean, wait minimum 1.2s so user sees pipeline steps
      await new Promise((resolve) => setTimeout(resolve, 1400));
      clearInterval(stepInterval);

      const enrichedDecision = {
        ...result,
        ...payload,
        risk_score: result.risk_score,
        decision: result.decision,
        reasons: result.reasons,
        latency_ms: result.latency_ms,
        transaction_id: result.transaction_id,
        timestamp: payload.timestamp
      };

      setDecisionResult(enrichedDecision);

      // Save transaction to global feed
      if (onAddTransaction) {
        onAddTransaction(enrichedDecision);
      }

      // Branch based on decision
      if (result.decision === 'ALLOW') {
        setCurrentStep('ALLOW_RECEIPT');
        addToast({
          type: 'success',
          title: 'Transaction Approved',
          message: `Score: ${result.risk_score}/100. Verification passed in ${result.latency_ms}ms.`
        });
      } else if (result.decision === 'WARN') {
        setCurrentStep('WARN_CONFIRMATION');
        addToast({
          type: 'warning',
          title: 'Security Warning',
          message: `Elevated risk score (${result.risk_score}/100). Review detected factors.`
        });
      } else {
        // HOLD
        setCurrentStep('HOLD_BLOCKED');
        addToast({
          type: 'error',
          title: 'Transaction On Hold',
          message: `High risk score (${result.risk_score}/100). Payment halted to protect account.`
        });
      }
    } catch (err) {
      clearInterval(stepInterval);
      addToast({
        type: 'error',
        title: 'Scoring Error',
        message: err.message || 'Failed to complete risk evaluation.'
      });
      setCurrentStep('FORM');
    }
  };

  // When user in WARN step explicitly proceeds
  const handleWarnProceed = () => {
    addToast({
      type: 'warning',
      title: 'Manual Override Accepted',
      message: 'Transaction processed following explicit user consent.'
    });
    setCurrentStep('ALLOW_RECEIPT');
  };

  // When user in WARN step cancels
  const handleWarnCancel = () => {
    addToast({
      type: 'info',
      title: 'Payment Cancelled',
      message: 'Cancelled safely. No funds were debited from your account.'
    });
    handleReset();
  };

  const handleReset = () => {
    setCurrentStep('FORM');
    setDecisionResult(null);
    setCurrentTransaction(null);
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      
      {/* Visual Pipeline Progress Modal / Indicator during ANALYZING */}
      {currentStep === 'ANALYZING' && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="max-w-md w-full fintech-card rounded-3xl p-6 sm:p-8 border border-cyan-500/40 cyan-glow animate-scale-up text-center">
            
            <div className="w-16 h-16 mx-auto rounded-2xl bg-cyan-950 border border-cyan-400 flex items-center justify-center mb-5 relative">
              <Cpu className="w-8 h-8 text-accent-cyan-bright animate-spin" style={{ animationDuration: '4s' }} />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-cyan-400 rounded-full animate-ping" />
            </div>

            <h3 className="text-lg font-bold text-white tracking-tight">
              AI Risk Pipeline In Progress
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Evaluating transaction parameters across neural graph & rule engines
            </p>

            {/* Stages progress list */}
            <div className="mt-6 space-y-3 text-left">
              {stages.map((stageText, idx) => {
                const isPassed = idx < stageIndex;
                const isCurrent = idx === stageIndex;

                return (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-2.5 rounded-xl border text-xs transition-all ${
                      isPassed
                        ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                        : isCurrent
                        ? 'bg-cyan-950/50 border-cyan-400 text-cyan-200 shadow-md shadow-cyan-500/10'
                        : 'bg-navy-950/40 border-surface-border text-slate-500'
                    }`}
                  >
                    <div className="shrink-0">
                      {isPassed ? (
                        <div className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">
                          ✓
                        </div>
                      ) : isCurrent ? (
                        <div className="w-4 h-4 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                      ) : (
                        <div className="w-4 h-4 rounded-full bg-slate-800 text-slate-600 flex items-center justify-center text-[10px]">
                          {idx + 1}
                        </div>
                      )}
                    </div>
                    <span className="truncate">{stageText}</span>
                  </div>
                );
              })}
            </div>

            <p className="text-[11px] font-mono text-cyan-400 mt-6">
              POST /api/transactions/score
            </p>
          </div>
        </div>
      )}

      {/* View routing based on step */}
      {currentStep === 'FORM' && (
        <PaymentForm
          onAnalyzeAndPay={handleStartAnalysis}
          isAnalyzing={false}
          currentStageText=""
        />
      )}

      {currentStep === 'ALLOW_RECEIPT' && (
        <div className="space-y-6">
          <PaymentReceipt
            transaction={decisionResult}
            onReset={handleReset}
          />
        </div>
      )}

      {currentStep === 'WARN_CONFIRMATION' && (
        <WarnDecisionModal
          decisionData={decisionResult}
          onProceed={handleWarnProceed}
          onCancel={handleWarnCancel}
        />
      )}

      {currentStep === 'HOLD_BLOCKED' && (
        <HoldDecisionScreen
          decisionData={decisionResult}
          onReset={handleReset}
        />
      )}

    </div>
  );
}
