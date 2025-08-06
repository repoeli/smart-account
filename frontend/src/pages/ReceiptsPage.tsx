const ReceiptsPage = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Receipts</h1>
      
      <div className="card text-center py-12">
        <div className="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-gray-400 text-2xl">📄</span>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No receipts yet</h3>
        <p className="text-gray-500 mb-6">
          Upload your first receipt to get started with smart organization and OCR processing.
        </p>
        <button className="btn-primary">
          📤 Upload Your First Receipt
        </button>
      </div>
    </div>
  );
};

export default ReceiptsPage;