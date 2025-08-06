import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';
import type { Folder, CreateFolderRequest } from '../../types/api';

interface FoldersState {
  folders: Folder[];
  currentFolder: Folder | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: FoldersState = {
  folders: [],
  currentFolder: null,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchFolders = createAsyncThunk(
  'folders/fetchFolders',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.getFolders();
      return response.folders;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch folders');
    }
  }
);

export const createFolder = createAsyncThunk(
  'folders/createFolder',
  async (data: CreateFolderRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.createFolder(data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create folder');
    }
  }
);

export const updateFolder = createAsyncThunk(
  'folders/updateFolder',
  async ({ id, data }: { id: string; data: { new_parent_id?: string } }, { rejectWithValue }) => {
    try {
      const response = await apiClient.updateFolder(id, data);
      return { id, response };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update folder');
    }
  }
);

export const moveReceiptsToFolder = createAsyncThunk(
  'folders/moveReceiptsToFolder',
  async ({ folderId, receiptIds }: { folderId: string; receiptIds: string[] }, { rejectWithValue }) => {
    try {
      const response = await apiClient.moveReceiptsToFolder(folderId, receiptIds);
      return { folderId, receiptIds, response };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to move receipts');
    }
  }
);

const foldersSlice = createSlice({
  name: 'folders',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentFolder: (state, action: PayloadAction<Folder | null>) => {
      state.currentFolder = action.payload;
    },
    updateFolderReceiptCount: (state, action: PayloadAction<{ folderId: string; count: number }>) => {
      const folder = state.folders.find((f) => f.id === action.payload.folderId);
      if (folder) {
        folder.receipt_count = action.payload.count;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch folders
    builder
      .addCase(fetchFolders.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchFolders.fulfilled, (state, action) => {
        state.isLoading = false;
        state.folders = action.payload;
      })
      .addCase(fetchFolders.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Create folder
    builder
      .addCase(createFolder.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createFolder.fulfilled, (state) => {
        state.isLoading = false;
        // Refresh folders after creation
      })
      .addCase(createFolder.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Update folder
    builder
      .addCase(updateFolder.fulfilled, () => {
        // Refresh folders after update
      })
      .addCase(updateFolder.rejected, (state, action) => {
        state.error = action.payload as string;
      });

    // Move receipts to folder
    builder
      .addCase(moveReceiptsToFolder.fulfilled, (state, action) => {
        const { folderId, receiptIds } = action.payload;
        const folder = state.folders.find((f) => f.id === folderId);
        if (folder) {
          folder.receipt_count += receiptIds.length;
        }
      })
      .addCase(moveReceiptsToFolder.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const { clearError, setCurrentFolder, updateFolderReceiptCount } = foldersSlice.actions;
export default foldersSlice.reducer;