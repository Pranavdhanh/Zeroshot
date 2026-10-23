import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  ShieldCheck,
  Activity,
  History,
  LayoutDashboard,
  GitFork,
  Briefcase,
  Languages,
  RefreshCw,
  Menu,
  X,
  Server
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useBackendStatus } from '../../context/BackendStatusContext';

export default function Navbar() {
  const { lang, toggleLanguage, t } = useLanguage();
  const { isOnline, latencyMs, checking, refreshStatus, apiBaseUrl } = useBackendStatus();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { to: '/', label: t('nav_simulator'), icon: ShieldCheck, exact: true },
    { to: '/transactions', label: t('nav_transactions'), icon: History },
    { to: '/dashboard', label: t('nav_dashboard'), icon: LayoutDashboard },
    { to: '/network', label: t('nav_network'), icon: GitFork },
    { to: '/cases', label: t('nav_cases'), icon: Briefcase },
  ];

  return (
    <header className="sticky top-0 z-40 bg-navy-950/90 backdrop-blur-md border-b border-surface-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo & College Track */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-all">
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-base tracking-tight text-white group-hover:text-accent-cyan-bright transition-colors">
                    UPI Shield <span className="text-accent-cyan-bright">AI</span>
                  </span>
                  <span className="hidden sm:inline-flex px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-cyan-950/70 border border-cyan-800/60 text-cyan-400">
                    VIT Hackathon
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 truncate max-w-[200px] sm:max-w-none">
                  Track 4: FinTech & GovTech Intelligence
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.exact}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-surface-elevated text-accent-cyan-bright border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                        : 'text-slate-300 hover:text-white hover:bg-surface'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Right Action Controls: Backend Status & Language Toggle */}
          <div className="flex items-center gap-2.5">
            {/* Backend Connectivity Pill */}
            <div
              className={`hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-mono border transition-all ${
                isOnline
                  ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300'
                  : 'bg-amber-950/50 border-amber-500/30 text-amber-300'
              }`}
              title={`API Base: ${apiBaseUrl} (Click to re-ping)`}
            >
              <div className="relative flex h-2 w-2">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    isOnline ? 'bg-emerald-400' : 'bg-amber-400'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    isOnline ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                />
              </div>
              <span className="text-[11px] font-sans font-medium">
                {isOnline ? t('status_connected') : t('status_offline')}
              </span>
              {isOnline && latencyMs !== null && (
                <span className="text-[10px] text-emerald-400/80 font-mono">
                  {latencyMs}ms
                </span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  refreshStatus();
                }}
                disabled={checking}
                className="hover:text-white text-slate-400 transition-colors p-0.5"
                title="Refresh backend status"
              >
                <RefreshCw className={`w-3 h-3 ${checking ? 'animate-spin text-cyan-400' : ''}`} />
              </button>
            </div>

            {/* Language Switcher Button (English / தமிழ்) */}
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface border border-surface-border hover:border-cyan-500/40 text-slate-200 hover:text-white transition-all text-xs font-medium"
              title="Toggle English / தமிழ் Language"
            >
              <Languages className="w-3.5 h-3.5 text-accent-cyan-bright" />
              <span className="font-semibold">{lang === 'en' ? 'தமிழ்' : 'English'}</span>
            </button>

            {/* Mobile Menu Toggle Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg bg-surface border border-surface-border text-slate-300 hover:text-white"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Navigation */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-3 px-2 border-t border-surface-border bg-navy-950 animate-slide-down space-y-1">
            <div className="px-3 py-2 flex items-center justify-between text-xs font-mono rounded bg-surface/50 border border-surface-border mb-2">
              <span className="text-slate-400">FastAPI Backend:</span>
              <span className={isOnline ? 'text-emerald-400' : 'text-amber-400'}>
                {isOnline ? `Connected (${latencyMs || 0}ms)` : 'Offline (Demo Fallback)'}
              </span>
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.exact}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-surface-elevated text-accent-cyan-bright border border-cyan-500/30'
                        : 'text-slate-300 hover:bg-surface hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        )}
      </div>
    </header>
  );
}
