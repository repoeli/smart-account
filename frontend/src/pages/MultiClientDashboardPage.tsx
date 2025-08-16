import React, { useEffect, useState } from 'react';
import { apiClient } from '../services/api';
import { Link } from 'react-router-dom';

interface ClientItem {
  id: string;
  name: string;
  email?: string;
  company_name?: string;
  status?: string;
}

const MultiClientDashboardPage: React.FC = () => {
  const [clients, setClients] = useState<ClientItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        setLoading(true);
        const response = await apiClient.getClients();
        if (response.success) {
          setClients(response.items);
        } else {
          setError('Failed to fetch clients.');
        }
      } catch (err) {
        setError('An error occurred while fetching clients.');
      } finally {
        setLoading(false);
      }
    };

    fetchClients();
  }, []);

  if (loading) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading clients...</div></div>;
  }

  if (error) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error}</div></div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Multi-Client Dashboard</h1>
      <div className="card">
        <div className="card-body">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Name</th>
                <th className="py-2">Email</th>
                <th className="py-2">Company</th>
                <th className="py-2">Status</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {clients.map(client => (
                <tr key={client.id} className="border-b last:border-0">
                  <td className="py-2">{client.name}</td>
                  <td className="py-2">{client.email || '-'}</td>
                  <td className="py-2">{client.company_name || '-'}</td>
                  <td className="py-2">{client.status || '-'}</td>
                  <td className="py-2">
                    <Link to={`/clients/${client.id}`} className="btn btn-sm">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MultiClientDashboardPage;
