import React, { useState } from 'react';
import {
  ShieldCheck,
  Send,
  User,
  AtSign,
  IndianRupee,
  FileText,
  Smartphone,
  AlertCircle,
  Sparkles,
  ChevronDown,
  Building,
  CheckCircle2,
  Clock,
  Layers
} from 'lucide-react';
import { SAMPLE_SENDERS, RECIPIENT_PRESETS } from '../../data/mockData';
import { useLanguage } from '../../context/LanguageContext';

export default function PaymentForm({ onAnalyzeAndPay, isAnalyzing, currentStageText }) {
  const { t } = useLanguage();

  const [selectedSender, setSelectedSender] = useState(SAMPLE_SENDERS[0]);
  const [recipientName, setRecipientName] = useState(RECIPIENT_PRESETS[0].name);
  const [recipientUpi, setRecipientUpi] = useState(RECIPIENT_PRESETS[0].upiId);
  const [recipientId, setRecipientId] = useState(RECIPIENT_PRESETS[0].id);
  const [amount, setAmount] = useState(RECIPIENT_PRESETS[0].suggestedAmount.toString());
  const [note, setNote] = useState(RECIPIENT_PRESETS[0].note);
  const [deviceChanged, setDeviceChanged] = useState(false);
  const [errors, setErrors] = useState({});

  // Preset filter tab
  const [presetTab, setPresetTab] = useState('all');

  const filteredPresets = RECIPIENT_PRESETS.filter((p) => {
    if (presetTab === 'known') return p.type === 'known';
    if (presetTab === 'new') return p.type === 'new';
    if (presetTab === 'suspicious') return p.type === 'suspicious';
    return true;
  });

  const handleApplyPreset = (preset) => {
    setRecipientName(preset.name);
    setRecipientUpi(preset.upiId);
    setRecipientId(preset.id);
    setAmount(preset.suggestedAmount.toString());
    setNote(preset.note);
    setErrors({});
  };

  const handleAmountChip = (val) => {
    setAmount(val.toString());
    if (errors.amount) {
      setErrors((prev) => ({ ...prev, amount: null }));
    }
  };

  const validate = () => {
    const errs = {};
    if (!recipientName.trim()) {
      errs.recipientName = 'Recipient name is required';
    }
    if (!recipientUpi.trim()) {
      errs.recipientUpi = 'Recipient UPI ID / VPA is required';
    } else if (!recipientUpi.includes('@')) {
      errs.recipientUpi = 'Valid UPI ID format required (e.g., user@bank)';
    }

    const numAmount = parseFloat(amount);
    if (!amount || isNaN(numAmount) || numAmount <= 0) {
      errs.amount = 'Please enter a valid positive amount in ₹';
    } else if (numAmount > selectedSender.balance) {
      errs.amount = `Amount exceeds account balance (₹${selectedSender.balance.toLocaleString('en-IN')})`;
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    onAnalyzeAndPay({
      sender_id: selectedSender.id,
      sender_name: selectedSender.name,
      sender_bank: selectedSender.bankName,
      sender_account: selectedSender.accountNumber,
      recipient_id: recipientId || recipientUpi,
      recipient_name: recipientName,
      recipient_upi: recipientUpi,
      amount: parseFloat(amount),
      note: note.trim(),
      timestamp: new Date().toISOString(),
      device_changed: deviceChanged
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      
      {/* Simulator Heading Card */}
      <div className="fintech-card rounded-3xl p-6 sm:p-7 border border-surface-border">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-surface-border">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-accent-cyan-bright animate-pulse" />
              <h2 className="text-xl font-bold tracking-tight text-white font-sans">
                {t('sim_title')}
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Indian UPI Interface with Pre-Transaction AI Shield Verification
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-navy-950/80 border border-cyan-500/20 text-accent-cyan-bright text-xs font-mono">
            <ShieldCheck className="w-4 h-4 text-accent-cyan-bright" />
            <span>Pre-Debit ML Intercept</span>
          </div>
        </div>

        {/* Quick Scenario Preset Chips */}
        <div className="pt-4 pb-2">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-accent-cyan-bright" />
              {t('sim_quick_presets')}
            </span>

            {/* Filter buttons */}
            <div className="flex items-center gap-1 bg-navy-950 p-1 rounded-lg border border-surface-border text-[11px]">
              <button
                type="button"
                onClick={() => setPresetTab('all')}
                className={`px-2 py-0.5 rounded ${presetTab === 'all' ? 'bg-surface-elevated text-white font-medium' : 'text-slate-400 hover:text-white'}`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setPresetTab('known')}
                className={`px-2 py-0.5 rounded ${presetTab === 'known' ? 'bg-emerald-950 text-emerald-300 font-medium' : 'text-slate-400 hover:text-white'}`}
              >
                Known
              </button>
              <button
                type="button"
                onClick={() => setPresetTab('new')}
                className={`px-2 py-0.5 rounded ${presetTab === 'new' ? 'bg-amber-950 text-amber-300 font-medium' : 'text-slate-400 hover:text-white'}`}
              >
                New
              </button>
              <button
                type="button"
                onClick={() => setPresetTab('suspicious')}
                className={`px-2 py-0.5 rounded ${presetTab === 'suspicious' ? 'bg-rose-950 text-rose-300 font-medium' : 'text-slate-400 hover:text-white'}`}
              >
                Mule/Scam
              </button>
            </div>
          </div>

          {/* Preset Cards Carousel / Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {filteredPresets.map((preset) => {
              const isSelected = recipientUpi === preset.upiId;
              const isHold = preset.expectedOutcome === 'HOLD';
              const isWarn = preset.expectedOutcome === 'WARN';

              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleApplyPreset(preset)}
                  className={`text-left p-2.5 rounded-xl border transition-all ${
                    isSelected
                      ? 'bg-surface-elevated border-cyan-500 shadow-md shadow-cyan-500/10'
                      : 'bg-navy-950/60 border-surface-border hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-100 truncate pr-1">
                      {preset.name}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                        isHold
                          ? 'bg-rose-950 text-rose-300 border border-rose-500/30'
                          : isWarn
                          ? 'bg-amber-950 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {preset.expectedOutcome}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 truncate">
                    {preset.upiId}
                  </div>
                  <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400">
                    <span>₹{preset.suggestedAmount.toLocaleString('en-IN')}</span>
                    <span className="text-slate-500 italic truncate max-w-[100px]">{preset.presetCategory}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          
          {/* Sender Account Picker */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              {t('sim_sender_label')}
            </label>
            <div className="relative">
              <select
                value={selectedSender.id}
                onChange={(e) => {
                  const s = SAMPLE_SENDERS.find((x) => x.id === e.target.value);
                  if (s) setSelectedSender(s);
                }}
                className="w-full bg-navy-950 border border-surface-border rounded-xl px-4 py-2.5 text-xs text-slate-100 font-sans focus:outline-none focus:border-cyan-500 appearance-none transition-colors"
              >
                {SAMPLE_SENDERS.map((sender) => (
                  <option key={sender.id} value={sender.id}>
                    {sender.name} ({sender.bankName} - {sender.accountNumber}) — Bal: ₹{sender.balance.toLocaleString('en-IN')}
                  </option>
                ))}
              </select>
              <div className="absolute right-3.5 top-3 pointer-events-none text-slate-400">
                <ChevronDown className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px] text-slate-400 px-1">
              <span>{selectedSender.device} • {selectedSender.city}</span>
              <span className="font-mono text-cyan-400">Bal: ₹{selectedSender.balance.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Recipient Details: Name and UPI ID */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                {t('sim_recipient_name')}
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={recipientName}
                  onChange={(e) => {
                    setRecipientName(e.target.value);
                    if (errors.recipientName) setErrors((prev) => ({ ...prev, recipientName: null }));
                  }}
                  placeholder="e.g., Ramesh Kumar"
                  className={`w-full bg-navy-950 border ${errors.recipientName ? 'border-rose-500' : 'border-surface-border'} rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors`}
                />
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              </div>
              {errors.recipientName && (
                <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.recipientName}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                {t('sim_recipient_label')}
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={recipientUpi}
                  onChange={(e) => {
                    setRecipientUpi(e.target.value);
                    setRecipientId(e.target.value);
                    if (errors.recipientUpi) setErrors((prev) => ({ ...prev, recipientUpi: null }));
                  }}
                  placeholder="e.g., ramesh@ybl"
                  className={`w-full bg-navy-950 border ${errors.recipientUpi ? 'border-rose-500' : 'border-surface-border'} rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-100 font-mono placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors`}
                />
                <AtSign className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              </div>
              {errors.recipientUpi && (
                <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.recipientUpi}
                </p>
              )}
            </div>
          </div>

          {/* Amount Field + Quick Amount Chips */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                {t('sim_amount_label')}
              </label>
              <span className="text-[11px] text-slate-400">INR Currency</span>
            </div>

            <div className="relative">
              <input
                type="number"
                min="1"
                step="any"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  if (errors.amount) setErrors((prev) => ({ ...prev, amount: null }));
                }}
                placeholder="Enter amount (e.g. 15000)"
                className={`w-full bg-navy-950 border ${errors.amount ? 'border-rose-500' : 'border-surface-border'} rounded-xl pl-10 pr-4 py-3 text-lg font-bold font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors`}
              />
              <span className="text-accent-cyan-bright font-bold text-lg absolute left-3.5 top-2.5">
                ₹
              </span>
            </div>
            {errors.amount && (
              <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> {errors.amount}
              </p>
            )}

            {/* Quick Amount Chips */}
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wide">Presets:</span>
              {[500, 2000, 5000, 15000, 45000, 60000].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => handleAmountChip(val)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium border transition-all ${
                    amount === val.toString()
                      ? 'bg-cyan-950 border-cyan-400 text-cyan-300'
                      : 'bg-navy-950 border-surface-border text-slate-300 hover:border-slate-500'
                  }`}
                >
                  ₹{val.toLocaleString('en-IN')}
                </button>
              ))}
            </div>
          </div>

          {/* Optional Note */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              {t('sim_note_label')}
            </label>
            <div className="relative">
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder={t('sim_note_placeholder')}
                className="w-full bg-navy-950 border border-surface-border rounded-xl pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
              />
              <FileText className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            </div>
          </div>

          {/* Device Changed / Security Telemetry Simulation Toggle */}
          <div className="p-3.5 rounded-xl bg-navy-950/80 border border-surface-border flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <Smartphone className={`w-4 h-4 mt-0.5 shrink-0 ${deviceChanged ? 'text-amber-400' : 'text-slate-400'}`} />
              <div>
                <label htmlFor="device-toggle" className="text-xs font-semibold text-slate-200 cursor-pointer">
                  {t('sim_device_toggle')}
                </label>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {t('sim_device_desc')}
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                id="device-toggle"
                type="checkbox"
                checked={deviceChanged}
                onChange={(e) => setDeviceChanged(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500"></div>
            </label>
          </div>

          {/* Academic Simulation Notice */}
          <div className="text-center pt-1">
            <p className="text-[11px] text-slate-500">
              {t('sim_disclaimer')}
            </p>
          </div>

          {/* Submit / Analyze & Pay Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isAnalyzing}
              className={`w-full flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-2xl font-bold text-sm tracking-wide transition-all shadow-lg ${
                isAnalyzing
                  ? 'bg-cyan-900/60 text-cyan-200 border border-cyan-500/40 cursor-wait'
                  : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-navy-950 shadow-cyan-500/25 hover:shadow-cyan-500/40'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-cyan-300 border-t-transparent rounded-full animate-spin" />
                  <span>{currentStageText || t('sim_btn_analyzing')}</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>{t('sim_btn_analyze_pay')}</span>
                  <span className="font-mono text-xs opacity-80">(₹{Number(amount || 0).toLocaleString('en-IN')})</span>
                </>
              )}
            </button>
          </div>

        </form>

      </div>

    </div>
  );
}
