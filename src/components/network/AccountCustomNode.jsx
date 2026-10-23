import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { ShieldAlert, ShieldCheck, AlertTriangle, User, Building, HardDrive } from 'lucide-react';

function AccountCustomNode({ data, selected }) {
  const {
    name,
    upi,
    role = 'Account',
    riskScore = 10,
    balance,
    status = 'Active'
  } = data;

  const isCritical = riskScore >= 80;
  const isWarn = riskScore >= 40 && riskScore < 80;
  const isSafe = riskScore < 40;

  const borderColor = isCritical
    ? selected ? 'border-rose-400 ring-2 ring-rose-500/50' : 'border-rose-500/60'
    : isWarn
    ? selected ? 'border-amber-400 ring-2 ring-amber-500/50' : 'border-amber-500/60'
    : selected ? 'border-cyan-400 ring-2 ring-cyan-500/50' : 'border-emerald-500/50';

  const badgeBg = isCritical
    ? 'bg-rose-950 text-rose-300 border-rose-500/40'
    : isWarn
    ? 'bg-amber-950 text-amber-300 border-amber-500/40'
    : 'bg-emerald-950 text-emerald-300 border-emerald-500/40';

  return (
    <div
      className={`min-w-[190px] max-w-[220px] rounded-2xl bg-navy-950/95 p-3.5 border shadow-xl backdrop-blur-md transition-all ${borderColor} ${
        isCritical ? 'shadow-rose-950/30' : isWarn ? 'shadow-amber-950/30' : 'shadow-cyan-950/20'
      }`}
    >
      {/* Target input handle (left) */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-cyan-400 border-2 border-navy-950"
      />

      {/* Node Header */}
      <div className="flex items-center justify-between gap-1 pb-1.5 border-b border-surface-border">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 truncate max-w-[100px]">
          {role}
        </span>
        <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${badgeBg}`}>
          {riskScore}/100
        </span>
      </div>

      {/* Account Info */}
      <div className="mt-2 space-y-0.5">
        <div className="text-xs font-bold text-white truncate font-sans">
          {name}
        </div>
        <div className="text-[10px] font-mono text-cyan-400 truncate">
          {upi}
        </div>
      </div>

      {/* Balance & Status Footer */}
      <div className="mt-2.5 pt-1.5 border-t border-surface-border flex items-center justify-between text-[10px]">
        <span className="text-slate-400">{balance}</span>
        <span
          className={`font-medium ${
            isCritical ? 'text-rose-400' : isWarn ? 'text-amber-400' : 'text-emerald-400'
          }`}
        >
          {status}
        </span>
      </div>

      {/* Source output handle (right) */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-accent-cyan-bright border-2 border-navy-950"
      />
    </div>
  );
}

export default memo(AccountCustomNode);
