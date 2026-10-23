import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import { ToastProvider } from './context/ToastContext';
import { BackendStatusProvider } from './context/BackendStatusContext';

import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';

import PaymentSimulatorPage from './pages/PaymentSimulatorPage';
import TransactionsPage from './pages/TransactionsPage';
import DashboardPage from './pages/DashboardPage';
import MuleNetworkPage from './pages/MuleNetworkPage';
import CaseManagementPage from './pages/CaseManagementPage';

export default function App() {
  const [localTransactions, setLocalTransactions] = useState([]);

  const handleAddTransaction = (newTx) => {
    setLocalTransactions((prev) => [newTx, ...prev]);
  };

  return (
    <LanguageProvider>
      <BackendStatusProvider>
        <ToastProvider>
          <BrowserRouter>
            <div className="flex flex-col min-h-screen bg-navy-900 text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-white">
              <Navbar />
              
              <main className="flex-1">
                <Routes>
                  <Route
                    path="/"
                    element={<PaymentSimulatorPage onAddTransaction={handleAddTransaction} />}
                  />
                  <Route
                    path="/transactions"
                    element={<TransactionsPage localTransactions={localTransactions} />}
                  />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/network" element={<MuleNetworkPage />} />
                  <Route path="/cases" element={<CaseManagementPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </main>

              <Footer />
            </div>
          </BrowserRouter>
        </ToastProvider>
      </BackendStatusProvider>
    </LanguageProvider>
  );
}
