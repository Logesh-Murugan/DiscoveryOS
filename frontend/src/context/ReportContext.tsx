import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { ReportResponse } from '../types';

interface ReportContextType {
  reportData: ReportResponse | null;
  setReportData: (data: ReportResponse | null) => void;
}

const ReportContext = createContext<ReportContextType | undefined>(undefined);

export const ReportProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [reportData, setReportData] = useState<ReportResponse | null>(null);

  return (
    <ReportContext.Provider value={{ reportData, setReportData }}>
      {children}
    </ReportContext.Provider>
  );
};

export const useReport = (): ReportContextType => {
  const context = useContext(ReportContext);
  if (!context) {
    throw new Error('useReport must be used within a ReportProvider');
  }
  return context;
};
