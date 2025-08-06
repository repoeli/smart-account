import { useParams } from 'react-router-dom';

const ReceiptDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Receipt Details</h1>
      
      <div className="card text-center py-12">
        <p className="text-gray-500">
          Receipt detail page for ID: {id}
        </p>
        <p className="text-sm text-gray-400 mt-2">
          This page will show detailed receipt information, OCR data, and editing options.
        </p>
      </div>
    </div>
  );
};

export default ReceiptDetailPage;