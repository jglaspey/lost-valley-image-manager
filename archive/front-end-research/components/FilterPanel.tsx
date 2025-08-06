import { useState } from 'react';
import { ChevronDown, ChevronUp, X } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Checkbox } from './ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { SearchFilters, ActivityTag } from '../types/image';
import { activityTagLabels } from '../data/mockImages';

interface FilterPanelProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  isOpen: boolean;
  onToggle: () => void;
  activeFilterCount: number;
}

export function FilterPanel({ filters, onFiltersChange, isOpen, onToggle, activeFilterCount }: FilterPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['quality', 'activity']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const clearAllFilters = () => {
    onFiltersChange({
      query: '',
      visualQuality: [1, 5],
      hasPeople: undefined,
      peopleCount: [],
      isIndoor: undefined,
      activityTags: [],
      season: [],
      timeOfDay: [],
      socialMediaScore: [1, 5],
      marketingScore: [1, 5]
    });
  };

  const toggleActivityTag = (tag: ActivityTag) => {
    const newTags = filters.activityTags.includes(tag)
      ? filters.activityTags.filter(t => t !== tag)
      : [...filters.activityTags, tag];
    onFiltersChange({ ...filters, activityTags: newTags });
  };

  const toggleArrayFilter = (key: keyof SearchFilters, value: string) => {
    const currentArray = filters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    onFiltersChange({ ...filters, [key]: newArray });
  };

  return (
    <Card className={`transition-all duration-300 ${isOpen ? 'w-80' : 'w-0 overflow-hidden'}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg">Filters</CardTitle>
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <Badge variant="secondary">{activeFilterCount}</Badge>
          )}
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            Clear All
          </Button>
          <Button variant="ghost" size="sm" onClick={onToggle}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {/* Visual Quality */}
        <Collapsible open={expandedSections.has('quality')} onOpenChange={() => toggleSection('quality')}>
          <CollapsibleTrigger className="flex items-center justify-between w-full">
            <Label className="font-medium">Visual Quality</Label>
            {expandedSections.has('quality') ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-3 pt-2">
            <div className="px-3">
              <Slider
                value={filters.visualQuality}
                onValueChange={(value) => onFiltersChange({ ...filters, visualQuality: value as [number, number] })}
                max={5}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-muted-foreground mt-1">
                <span>{filters.visualQuality[0]} (Poor)</span>
                <span>{filters.visualQuality[1]} (Excellent)</span>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* People */}
        <Collapsible open={expandedSections.has('people')} onOpenChange={() => toggleSection('people')}>
          <CollapsibleTrigger className="flex items-center justify-between w-full">
            <Label className="font-medium">People</Label>
            {expandedSections.has('people') ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="has-people"
                checked={filters.hasPeople === true}
                onCheckedChange={(checked) => 
                  onFiltersChange({ ...filters, hasPeople: checked ? true : undefined })
                }
              />
              <Label htmlFor="has-people">Has People</Label>
            </div>
            <div className="space-y-2">
              <Label className="text-sm">People Count</Label>
              {['1-2', '3-5', '6-10', '10+'].map((count) => (
                <div key={count} className="flex items-center space-x-2">
                  <Checkbox
                    id={`people-${count}`}
                    checked={filters.peopleCount.includes(count)}
                    onCheckedChange={() => toggleArrayFilter('peopleCount', count)}
                  />
                  <Label htmlFor={`people-${count}`} className="text-sm">{count} people</Label>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Setting */}
        <Collapsible open={expandedSections.has('setting')} onOpenChange={() => toggleSection('setting')}>
          <CollapsibleTrigger className="flex items-center justify-between w-full">
            <Label className="font-medium">Setting</Label>
            {expandedSections.has('setting') ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="indoor"
                checked={filters.isIndoor === true}
                onCheckedChange={(checked) => 
                  onFiltersChange({ ...filters, isIndoor: checked ? true : undefined })
                }
              />
              <Label htmlFor="indoor">Indoor Only</Label>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Activity Tags */}
        <Collapsible open={expandedSections.has('activity')} onOpenChange={() => toggleSection('activity')}>
          <CollapsibleTrigger className="flex items-center justify-between w-full">
            <Label className="font-medium">Activities</Label>
            {expandedSections.has('activity') ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-2 pt-2">
            <div className="grid grid-cols-1 gap-2">
              {Object.entries(activityTagLabels).map(([tag, label]) => (
                <div key={tag} className="flex items-center space-x-2">
                  <Checkbox
                    id={`activity-${tag}`}
                    checked={filters.activityTags.includes(tag as ActivityTag)}
                    onCheckedChange={() => toggleActivityTag(tag as ActivityTag)}
                  />
                  <Label htmlFor={`activity-${tag}`} className="text-sm">{label}</Label>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Context */}
        <Collapsible open={expandedSections.has('context')} onOpenChange={() => toggleSection('context')}>
          <CollapsibleTrigger className="flex items-center justify-between w-full">
            <Label className="font-medium">Context</Label>
            {expandedSections.has('context') ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-3 pt-2">
            <div className="space-y-2">
              <Label className="text-sm">Season</Label>
              {['spring', 'summer', 'fall', 'winter'].map((season) => (
                <div key={season} className="flex items-center space-x-2">
                  <Checkbox
                    id={`season-${season}`}
                    checked={filters.season.includes(season)}
                    onCheckedChange={() => toggleArrayFilter('season', season)}
                  />
                  <Label htmlFor={`season-${season}`} className="text-sm capitalize">{season}</Label>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              <Label className="text-sm">Time of Day</Label>
              {['morning', 'midday', 'evening'].map((time) => (
                <div key={time} className="flex items-center space-x-2">
                  <Checkbox
                    id={`time-${time}`}
                    checked={filters.timeOfDay.includes(time)}
                    onCheckedChange={() => toggleArrayFilter('timeOfDay', time)}
                  />
                  <Label htmlFor={`time-${time}`} className="text-sm capitalize">{time}</Label>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Marketing Scores */}
        <Collapsible open={expandedSections.has('scores')} onOpenChange={() => toggleSection('scores')}>
          <CollapsibleTrigger className="flex items-center justify-between w-full">
            <Label className="font-medium">Scores</Label>
            {expandedSections.has('scores') ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4 pt-2">
            <div className="space-y-2">
              <Label className="text-sm">Social Media Score</Label>
              <div className="px-3">
                <Slider
                  value={filters.socialMediaScore}
                  onValueChange={(value) => onFiltersChange({ ...filters, socialMediaScore: value as [number, number] })}
                  max={5}
                  min={1}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground mt-1">
                  <span>{filters.socialMediaScore[0]}</span>
                  <span>{filters.socialMediaScore[1]}</span>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-sm">Marketing Score</Label>
              <div className="px-3">
                <Slider
                  value={filters.marketingScore}
                  onValueChange={(value) => onFiltersChange({ ...filters, marketingScore: value as [number, number] })}
                  max={5}
                  min={1}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground mt-1">
                  <span>{filters.marketingScore[0]}</span>
                  <span>{filters.marketingScore[1]}</span>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}