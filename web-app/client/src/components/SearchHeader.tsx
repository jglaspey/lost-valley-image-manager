import { Search, Filter, Grid, List, SlidersHorizontal } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ToggleGroup, ToggleGroupItem } from './ui/toggle-group';
import { SearchFilters } from '../types/image';

interface SearchHeaderProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  onToggleFilters: () => void;
  isFiltersOpen: boolean;
  activeFilterCount: number;
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
  resultCount: number;
}

export function SearchHeader({ 
  filters, 
  onFiltersChange, 
  onToggleFilters, 
  isFiltersOpen,
  activeFilterCount,
  viewMode,
  onViewModeChange,
  resultCount
}: SearchHeaderProps) {
  return (
    <div className="bg-background border-b p-4 space-y-4">
      {/* Main Search Bar */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search images by description, activities, or content..."
            value={filters.query}
            onChange={(e) => onFiltersChange({ ...filters, query: e.target.value })}
            className="pl-10"
          />
        </div>
        <Button 
          variant={isFiltersOpen ? "default" : "outline"} 
          onClick={onToggleFilters}
          className="flex items-center gap-2"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </div>

      {/* Quick Filters & Controls */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm text-muted-foreground">Quick filters:</span>
          
          {/* High Quality Quick Filter */}
          <Button
            variant={filters.visualQuality[0] >= 4 ? "default" : "outline"}
            size="sm"
            onClick={() => 
              onFiltersChange({ 
                ...filters, 
                visualQuality: filters.visualQuality[0] >= 4 ? [1, 5] : [4, 5] 
              })
            }
          >
            High Quality (4-5★)
          </Button>

          {/* Marketing Ready Quick Filter */}
          <Button
            variant={filters.marketingScore[0] >= 4 ? "default" : "outline"}
            size="sm"
            onClick={() => 
              onFiltersChange({ 
                ...filters, 
                marketingScore: filters.marketingScore[0] >= 4 ? [1, 5] : [4, 5] 
              })
            }
          >
            Marketing Ready (4-5★)
          </Button>

          {/* Has People Quick Filter */}
          <Button
            variant={filters.hasPeople === true ? "default" : "outline"}
            size="sm"
            onClick={() => 
              onFiltersChange({ 
                ...filters, 
                hasPeople: filters.hasPeople === true ? undefined : true 
              })
            }
          >
            With People
          </Button>

          {/* Outdoor Only Quick Filter */}
          <Button
            variant={filters.isIndoor === false ? "default" : "outline"}
            size="sm"
            onClick={() => 
              onFiltersChange({ 
                ...filters, 
                isIndoor: filters.isIndoor === false ? undefined : false 
              })
            }
          >
            Outdoor
          </Button>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {resultCount} images
          </span>
          
          <ToggleGroup type="single" value={viewMode} onValueChange={(value) => value && onViewModeChange(value as 'grid' | 'list')}>
            <ToggleGroupItem value="grid" aria-label="Grid view">
              <Grid className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem value="list" aria-label="List view">
              <List className="h-4 w-4" />
            </ToggleGroupItem>
          </ToggleGroup>
        </div>
      </div>
    </div>
  );
}