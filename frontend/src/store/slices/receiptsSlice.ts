import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';
import type {
  Receipt,
  ReceiptUploadRequest,
  SearchReceiptsRequest,
  BulkOperationRequest,
  AddTagsRequest,
} from '../../types/api';

interface ReceiptsState {
  receipts: Receipt[];
  currentReceipt: Receipt | null;
  totalCount: number;
  isLoading: boolean;
  isUploading: boolean;
  error: string | null;
  searchParams: SearchReceiptsRequest;
  selectedReceipts: string[];
}

const initialState: ReceiptsState = {
  receipts: [],
  currentReceipt: null,
  totalCount: 0,
  isLoading: false,
  isUploading: false,
  error: null,
  searchParams: {
    limit: 20,
    offset: 0,
    sort_field: 'date',
    sort_direction: 'desc',
  },
  selectedReceipts: [],
};

// Async thunks
export const uploadReceipt = createAsyncThunk(
  'receipts/upload',
  async (data: ReceiptUploadRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.uploadReceipt(data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Upload failed');
    }
  }
);

export const fetchReceipts = createAsyncThunk(
  'receipts/fetchReceipts',
  async (params: { limit?: number; offset?: number; folder_id?: string } | undefined, { rejectWithValue }) => {
    try {
      const response = await apiClient.getReceipts(params);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch receipts');
    }
  }
);

export const fetchReceipt = createAsyncThunk(
  'receipts/fetchReceipt',
  async (id: string, { rejectWithValue }) => {
    try {
      const receipt = await apiClient.getReceipt(id);
      return receipt;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch receipt');
    }
  }
);

export const updateReceipt = createAsyncThunk(
  'receipts/updateReceipt',
  async ({ id, data }: { id: string; data: Partial<Receipt> }, { rejectWithValue }) => {
    try {
      const receipt = await apiClient.updateReceipt(id, data);
      return receipt;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update receipt');
    }
  }
);

export const searchReceipts = createAsyncThunk(
  'receipts/searchReceipts',
  async (params: SearchReceiptsRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.searchReceipts(params);
      return { response, params };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Search failed');
    }
  }
);

export const reprocessReceipt = createAsyncThunk(
  'receipts/reprocessReceipt',
  async ({ id, ocrMethod }: { id: string; ocrMethod: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.reprocessReceipt(id, ocrMethod);
      return { id, response };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Reprocessing failed');
    }
  }
);

export const validateReceipt = createAsyncThunk(
  'receipts/validateReceipt',
  async ({ id, data }: { id: string; data: any }, { rejectWithValue }) => {
    try {
      const response = await apiClient.validateReceipt(id, data);
      return { id, response };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Validation failed');
    }
  }
);

export const categorizeReceipt = createAsyncThunk(
  'receipts/categorizeReceipt',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.categorizeReceipt(id);
      return { id, response };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Categorization failed');
    }
  }
);

export const addTagsToReceipt = createAsyncThunk(
  'receipts/addTagsToReceipt',
  async ({ id, data }: { id: string; data: AddTagsRequest }, { rejectWithValue }) => {
    try {
      const response = await apiClient.addTagsToReceipt(id, data);
      return { id, response, tags: data.tags };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to add tags');
    }
  }
);

export const bulkOperation = createAsyncThunk(
  'receipts/bulkOperation',
  async (data: BulkOperationRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.bulkOperation(data);
      return { response, operation: data };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Bulk operation failed');
    }
  }
);

const receiptsSlice = createSlice({
  name: 'receipts',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setSearchParams: (state, action: PayloadAction<Partial<SearchReceiptsRequest>>) => {
      state.searchParams = { ...state.searchParams, ...action.payload };
    },
    selectReceipt: (state, action: PayloadAction<string>) => {
      const id = action.payload;
      if (state.selectedReceipts.includes(id)) {
        state.selectedReceipts = state.selectedReceipts.filter((receiptId) => receiptId !== id);
      } else {
        state.selectedReceipts.push(id);
      }
    },
    selectAllReceipts: (state) => {
      state.selectedReceipts = state.receipts.map((receipt) => receipt.id);
    },
    clearSelection: (state) => {
      state.selectedReceipts = [];
    },
    clearCurrentReceipt: (state) => {
      state.currentReceipt = null;
    },
  },
  extraReducers: (builder) => {
    // Upload receipt
    builder
      .addCase(uploadReceipt.pending, (state) => {
        state.isUploading = true;
        state.error = null;
      })
      .addCase(uploadReceipt.fulfilled, (state) => {
        state.isUploading = false;
      })
      .addCase(uploadReceipt.rejected, (state, action) => {
        state.isUploading = false;
        state.error = action.payload as string;
      });

    // Fetch receipts
    builder
      .addCase(fetchReceipts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchReceipts.fulfilled, (state, action) => {
        state.isLoading = false;
        state.receipts = action.payload.receipts;
        state.totalCount = action.payload.total_count;
      })
      .addCase(fetchReceipts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch single receipt
    builder
      .addCase(fetchReceipt.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchReceipt.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentReceipt = action.payload;
      })
      .addCase(fetchReceipt.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Update receipt
    builder
      .addCase(updateReceipt.fulfilled, (state, action) => {
        const index = state.receipts.findIndex((receipt) => receipt.id === action.payload.id);
        if (index !== -1) {
          state.receipts[index] = action.payload;
        }
        if (state.currentReceipt?.id === action.payload.id) {
          state.currentReceipt = action.payload;
        }
      });

    // Search receipts
    builder
      .addCase(searchReceipts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(searchReceipts.fulfilled, (state, action) => {
        state.isLoading = false;
        state.receipts = action.payload.response.receipts;
        state.totalCount = action.payload.response.total_count;
        state.searchParams = action.payload.params;
      })
      .addCase(searchReceipts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Add tags to receipt
    builder
      .addCase(addTagsToReceipt.fulfilled, (state, action) => {
        const { id, tags } = action.payload;
        const receipt = state.receipts.find((r) => r.id === id);
        if (receipt) {
          receipt.tags = [...(receipt.tags || []), ...tags];
        }
        if (state.currentReceipt?.id === id) {
          state.currentReceipt.tags = [...(state.currentReceipt.tags || []), ...tags];
        }
      });

    // Bulk operation
    builder
      .addCase(bulkOperation.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(bulkOperation.fulfilled, (state) => {
        state.isLoading = false;
        state.selectedReceipts = [];
      })
      .addCase(bulkOperation.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  setSearchParams,
  selectReceipt,
  selectAllReceipts,
  clearSelection,
  clearCurrentReceipt,
} = receiptsSlice.actions;

export default receiptsSlice.reducer;