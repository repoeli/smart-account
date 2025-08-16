import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { apiClient } from '../services/api';

interface Client {
  id: string;
  name: string;
  email?: string;
  company_name?: string;
  phone?: string;
  address?: string;
  vat_number?: string;
  status?: string;
}

const ClientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClient = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const response = await apiClient.getClient(id);
        if (response.success) {
          setClient(response.client);
        } else {
          setError('Failed to fetch client details.');
        }
      } catch (err) {
        setError('An error occurred while fetching client details.');
      } finally {
        setLoading(false);
      }
    };

    fetchClient();
  }, [id]);

  if (loading) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading client...</div></div>;
  }

  if (error) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error}</div></div>;
  }

  if (!client) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Client not found.</div></div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">{client.name}</h1>
      <div className="card">
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p><strong>Email:</strong> {client.email || '-'}</p>
              <p><strong>Company Name:</strong> {client.company_name || '-'}</p>
              <p><strong>Phone:</strong> {client.phone || '-'}</p>
            </div>
            <div>
              <p><strong>Address:</strong> {client.address || '-'}</p>
              <p><strong>VAT Number:</strong> {client.vat_number || '-'}</p>
              <p><strong>Status:</strong> {client.status || '-'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClientDetailPage;
