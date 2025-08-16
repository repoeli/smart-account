import React from 'react';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

const ReportsPage: React.FC = () => {
  const downloadReport = async () => {
    try {
      const response = await apiClient.getFinancialReportCSV();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'financial_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('Failed to download report.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Financial Reports</h1>
      <div className="card">
        <div className="card-body">
          <p>This page will allow users to generate and download various financial reports, such as profit and loss statements, balance sheets, and expense reports.</p>
          <div className="mt-4">
            <button className="btn btn-primary" onClick={downloadReport}>
              Download Transaction Report (CSV)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
