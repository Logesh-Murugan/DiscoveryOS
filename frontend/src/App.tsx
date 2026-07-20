import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ReportProvider } from './context/ReportContext';
import { IngestionScreen } from './components/IngestionScreen';
import { DashboardScreen } from './components/DashboardScreen';

export const App: React.FC = () => {
  return (
    <ReportProvider>
      <Router>
        <Routes>
          <Route path="/" element={<IngestionScreen />} />
          <Route path="/dashboard" element={<DashboardScreen />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ReportProvider>
  );
};

export default App;
