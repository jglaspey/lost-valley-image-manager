import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { databaseApi } from '../api/client';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Button } from './ui/button';
import { Loader2, Database, RefreshCw } from 'lucide-react';

interface DatabaseInfo {
  name: string;
  displayName: string;
  path: string;
}

interface DatabasePickerProps {
  onDatabaseChange?: (database: string) => void;
  isAuthenticated?: boolean;
}

export const DatabasePicker: React.FC<DatabasePickerProps> = ({ onDatabaseChange, isAuthenticated = false }) => {
  const [selectedDb, setSelectedDb] = useState<string>('');
  const queryClient = useQueryClient();

  // Fetch available databases - only when authenticated
  const { data: databases, isLoading: isLoadingDatabases, refetch: refetchDatabases } = useQuery({
    queryKey: ['databases'],
    queryFn: async () => {
      const data = await databaseApi.getDatabases();
      return data.databases as DatabaseInfo[];
    },
    enabled: isAuthenticated,
  });

  // Fetch current database - only when authenticated
  const { data: currentDatabase, isLoading: isLoadingCurrent } = useQuery({
    queryKey: ['current-database'],
    queryFn: async () => {
      return await databaseApi.getCurrentDatabase();
    },
    enabled: isAuthenticated,
  });

  // Switch database mutation
  const switchDatabaseMutation = useMutation({
    mutationFn: async (database: string) => {
      return await databaseApi.switchDatabase(database);
    },
    onSuccess: (data) => {
      toast.success(`Successfully switched to ${data.database}`);
      // Invalidate all queries to refetch with new database
      queryClient.invalidateQueries();
      onDatabaseChange?.(data.database);
    },
    onError: (error: Error) => {
      toast.error(`Failed to switch database: ${error.message}`);
    },
  });

  const handleDatabaseChange = (database: string) => {
    setSelectedDb(database);
    switchDatabaseMutation.mutate(database);
  };

  const handleRefresh = () => {
    refetchDatabases();
    queryClient.invalidateQueries({ queryKey: ['current-database'] });
  };

  if (isLoadingDatabases || isLoadingCurrent) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Database className="h-4 w-4" />
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading databases...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Database className="h-4 w-4 text-gray-600" />
      <Select
        value={selectedDb || currentDatabase?.database}
        onValueChange={handleDatabaseChange}
        disabled={switchDatabaseMutation.isPending}
      >
        <SelectTrigger className="w-[220px] h-8 text-sm">
          <SelectValue placeholder="Select database...">
            {currentDatabase?.displayName || 'Select database...'}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {databases?.map((db) => (
            <SelectItem key={db.name} value={db.name}>
              <div className="flex flex-col">
                <span className="font-medium">{db.displayName}</span>
                <span className="text-xs text-gray-500">{db.name}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      <Button
        variant="outline"
        size="sm"
        onClick={handleRefresh}
        disabled={isLoadingDatabases}
        className="h-8 px-2"
      >
        <RefreshCw className={`h-3 w-3 ${isLoadingDatabases ? 'animate-spin' : ''}`} />
      </Button>
      
      {switchDatabaseMutation.isPending && (
        <div className="flex items-center gap-1 text-sm text-blue-600">
          <Loader2 className="h-3 w-3 animate-spin" />
          Switching...
        </div>
      )}
    </div>
  );
};