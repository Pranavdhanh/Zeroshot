import React from 'react';
import { ShieldAlert, Cpu, Heart, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="mt-auto border-t border-surface-border bg-navy-950 py-6 text-xs text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-accent-cyan-bright shrink-0" />
            <span className="font-semibold text-slate-200">UPI Shield AI</span>
            <span className="text-slate-600">|</span>
            <span>VIT College • Track 4: FinTech & GovTech Intelligence</span>
          </div>

          <div className="flex items-center gap-2 text-center text-slate-400">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Academic Hackathon Prototype • Zero real financial transactions processed</span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[11px]">
            <span>FastAPI + XGBoost Engine</span>
            <span>•</span>
            <span>React + React Flow UI</span>
          </div>

        </div>
      </div>
    </footer>
  );
}
