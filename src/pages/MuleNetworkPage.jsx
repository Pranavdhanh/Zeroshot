import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  GitFork,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Play,
  Info,
  Lock,
  ExternalLink,
  PhoneCall,
  X,
  Layers,
  ArrowRight,
  Server,
  AlertCircle
} from 'lucide-react';
import AccountCustomNode from '../components/network/AccountCustomNode';
import { fetchNetworkGraph, triggerMuleScenario } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useToast } from '../context/ToastContext';
import { useNavigate } from 'react-router-dom';

const nodeTypes = {
  accountNode: AccountCustomNode,
};

export default function MuleNetworkPage() {
  const { t } = useLanguage();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const [activeScenarioId, setActiveScenarioId] = useState('mule_ring_3tier');
  const [scenarioMeta, setScenarioMeta] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(true);
  const [simulating, setSimulating] = useState(false);

  const loadScenario = useCallback(async (scenarioId) => {
    setLoading(true);
    setSelectedNode(null);
    try {
      const res = await fetchNetworkGraph(scenarioId);
      setIsFallback(res.isFallback);
      const data = res.data;
      if (data) {
        setScenarioMeta({
          title: data.title,
          description: data.description
        });
        
        // Add markers and formatting to edges
        const enrichedEdges = (data.edges || []).map((e) => ({
          ...e,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 16,
            height: 16,
            color: e.style?.stroke || '#06B6D4'
          },
          labelStyle: { fill: '#F1F5F9', fontWeight: 600, fontSize: 10 },
          labelBgStyle: { fill: '#0B0F19', fillOpacity: 0.9, stroke: '#23324E', strokeWidth: 1 },
          labelBgPadding: [6, 3],
          labelBgBorderRadius: 4,
        }));

        setNodes(data.nodes || []);
        setEdges(enrichedEdges);
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Network Graph Error',
        message: err.message
      });
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges, addToast]);

  useEffect(() => {
    loadScenario(activeScenarioId);
  }, [activeScenarioId, loadScenario]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const handleRunBackendSimulation = async () => {
    setSimulating(true);
    try {
      const res = await triggerMuleScenario(activeScenarioId);
      if (!res.isFallback) {
        addToast({
          type: 'success',
          title: 'Backend Simulation Executed',
          message: 'FastAPI simulation pipeline generated live network transaction flow.'
        });
        loadScenario(activeScenarioId);
      } else {
        addToast({
          type: 'info',
          title: 'Demo Scenario Triggered',
          message: 'Endpoint POST /api/network/simulate not found on backend. Displaying calibrated topology.'
        });
      }
    } finally {
      setSimulating(false);
    }
  };

  const handleFreezeAccount = () => {
    if (!selectedNode) return;
    addToast({
      type: 'warning',
      title: 'VPA Frozen in Sandbox',
      message: `Account ${selectedNode.data.upi} placed on emergency debit hold.`
    });
    // Update local node state
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNode.id
          ? { ...n, data: { ...n.data, status: 'FROZEN & BLOCKED' } }
          : n
      )
    );
    setSelectedNode((prev) => prev ? { ...prev, data: { ...prev.data, status: 'FROZEN & BLOCKED' } } : null);
  };

  const handleEscalateI4C = () => {
    addToast({
      type: 'success',
      title: 'I4C Cyber Crime Report Filed',
      message: `Dossier for ${selectedNode?.data?.upi} transmitted to GovTech Investigation Desk.`
    });
    navigate('/cases');
  };

  // Connected edges for the selected node
  const connectedEdges = useMemo(() => {
    if (!selectedNode) return [];
    return edges.filter(
      (e) => e.source === selectedNode.id || e.target === selectedNode.id
    );
  }, [selectedNode, edges]);

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GitFork className="w-5 h-5 text-accent-cyan-bright" />
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              {t('net_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('net_subtitle')}
          </p>
        </div>

        {/* Scenario Switcher & Simulation Trigger */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="bg-navy-950 p-1 rounded-xl border border-surface-border flex items-center text-xs">
            <button
              onClick={() => setActiveScenarioId('mule_ring_3tier')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeScenarioId === 'mule_ring_3tier'
                  ? 'bg-surface-elevated text-accent-cyan-bright border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              1. 3-Tier Layering
            </button>
            <button
              onClick={() => setActiveScenarioId('fan_out_disbursement')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeScenarioId === 'fan_out_disbursement'
                  ? 'bg-surface-elevated text-accent-cyan-bright border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              2. Rapid Fan-Out
            </button>
            <button
              onClick={() => setActiveScenarioId('legitimate_merchant')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeScenarioId === 'legitimate_merchant'
                  ? 'bg-surface-elevated text-accent-cyan-bright border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              3. Normal Flow
            </button>
          </div>

          <button
            onClick={handleRunBackendSimulation}
            disabled={simulating}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-navy-950 font-bold text-xs transition-colors shadow-lg shadow-cyan-600/20"
            title="Trigger simulation (checks backend POST /api/network/simulate or runs local scenario)"
          >
            <Play className={`w-3.5 h-3.5 ${simulating ? 'animate-spin' : 'fill-current'}`} />
            <span>Simulate Scenario</span>
          </button>
        </div>
      </div>

      {/* Backend / Demo Indicator */}
      {isFallback ? (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>DEMO DATA:</strong> Backend <code>GET /api/network</code> is offline; visualizing calibrated mule ring topologies. Click any account node to inspect.
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300">
          <Server className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Live Graph Topology rendered from FastAPI <code>GET /api/network</code></span>
        </div>
      )}

      {/* Scenario Context Banner */}
      {scenarioMeta && (
        <div className="fintech-card rounded-2xl p-4 border border-surface-border flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div>
            <span className="font-bold text-slate-100 text-sm block">
              {scenarioMeta.title}
            </span>
            <p className="text-slate-400 mt-0.5 leading-relaxed">
              {scenarioMeta.description}
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0 text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Safe Node
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Tier-1 Mule
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Aggregator Hub
            </span>
          </div>
        </div>
      )}

      {/* React Flow Container + Node Inspection Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-[580px]">
        
        {/* Interactive Graph (3 columns) */}
        <div className="lg:col-span-3 fintech-card rounded-3xl border border-surface-border overflow-hidden relative min-h-[560px]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.3}
            maxZoom={1.5}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1E293B" gap={20} size={1} />
            <Controls className="bg-navy-950 border border-surface-border text-slate-300 rounded-xl" />
            <MiniMap
              nodeColor={(n) => {
                const s = n.data?.riskScore || 0;
                return s >= 80 ? '#EF4444' : s >= 40 ? '#F59E0B' : '#10B981';
              }}
              maskColor="rgba(11, 15, 25, 0.75)"
              className="bg-navy-950 border border-surface-border rounded-xl"
            />
          </ReactFlow>

          {/* Canvas Overlay Tip */}
          <div className="absolute top-4 left-4 pointer-events-none bg-navy-950/80 backdrop-blur-sm border border-surface-border px-3 py-1.5 rounded-lg text-[10px] text-slate-400">
            Drag to pan • Scroll to zoom • Click node to inspect details
          </div>
        </div>

        {/* Node Inspection Panel (1 column) */}
        <div className="fintech-card rounded-3xl p-5 border border-surface-border flex flex-col justify-between">
          {selectedNode ? (
            <div className="space-y-4 animate-fade-in text-xs">
              
              <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Account Dossier
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Profile Card */}
              <div className="space-y-2">
                <h3 className="text-base font-bold text-white font-sans">
                  {selectedNode.data.name}
                </h3>
                <div className="font-mono text-cyan-400 text-xs">
                  {selectedNode.data.upi}
                </div>
                <div className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-surface border border-surface-border text-slate-300">
                  {selectedNode.data.role}
                </div>
              </div>

              {/* Risk Meter */}
              <div className="p-3 rounded-xl bg-navy-950 border border-surface-border space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-[11px]">Calculated Anomaly:</span>
                  <span
                    className={`font-mono font-bold text-sm ${
                      selectedNode.data.riskScore >= 80
                        ? 'text-rose-400'
                        : selectedNode.data.riskScore >= 40
                        ? 'text-amber-400'
                        : 'text-emerald-400'
                    }`}
                  >
                    {selectedNode.data.riskScore} / 100
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-[11px]">Status:</span>
                  <span className="font-medium text-slate-200">{selectedNode.data.status}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-[11px]">Reported Balance:</span>
                  <span className="font-bold text-white font-mono">{selectedNode.data.balance}</span>
                </div>
                {selectedNode.data.transitTime && (
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-[11px]">Fund Retention Window:</span>
                    <span className="text-amber-400 font-mono">{selectedNode.data.transitTime}</span>
                  </div>
                )}
              </div>

              {/* Connected Transfers */}
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                  Connected Flow Streams ({connectedEdges.length})
                </span>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {connectedEdges.map((e) => {
                    const isInbound = e.target === selectedNode.id;
                    return (
                      <div
                        key={e.id}
                        className="p-2 rounded-lg bg-navy-950 border border-surface-border flex items-center justify-between text-[11px]"
                      >
                        <span className={isInbound ? 'text-emerald-400 font-medium' : 'text-amber-400 font-medium'}>
                          {isInbound ? '← Inflow' : '→ Outflow'}
                        </span>
                        <span className="font-mono text-white font-semibold">{e.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Analyst Actions */}
              <div className="pt-3 space-y-2">
                <button
                  onClick={handleFreezeAccount}
                  className="w-full flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-navy-950 font-bold text-xs transition-colors"
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span>{t('net_btn_freeze')}</span>
                </button>
                <button
                  onClick={handleEscalateI4C}
                  className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-surface border border-rose-500/40 hover:bg-rose-950/40 text-rose-300 font-semibold text-xs transition-colors"
                >
                  <PhoneCall className="w-3.5 h-3.5" />
                  <span>{t('net_btn_escalate')}</span>
                </button>
              </div>

            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3 text-slate-500">
              <GitFork className="w-10 h-10 text-slate-600" />
              <div>
                <h4 className="text-sm font-semibold text-slate-300">No Account Selected</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Click any node in the React Flow graph to inspect account risk, transit velocity, and connected transfers.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
