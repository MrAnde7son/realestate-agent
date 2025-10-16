"use client";

import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/Badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Filter, X } from "lucide-react";

interface DocumentSearchProps {
  assetId?: number;
  onResultsChange: (results: {
    type: "params" | "reset";
    query: string;
    category: string;
    assetId?: number;
  }) => void;
  className?: string;
}

const DOCUMENT_CATEGORIES = [
  { value: "all", label: "כל הקטגוריות" },
  { value: "שומות", label: "שומות" },
  { value: "היתרים", label: "היתרים" },
  { value: "תוכניות", label: "תוכניות" },
  { value: "נסחים", label: "נסחים" },
  { value: "תשריטים", label: "תשריטים" },
  { value: "אחר", label: "אחר" },
];

export default function DocumentSearch({
  assetId,
  onResultsChange,
  className = "",
}: DocumentSearchProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [hasActiveFilters, setHasActiveFilters] = useState(false);

  // Check if there are active filters
  useEffect(() => {
    setHasActiveFilters(searchQuery.trim() !== "" || selectedCategory !== "all");
  }, [searchQuery, selectedCategory]);

  const handleSearch = async () => {
    onResultsChange({
      type: "params",
      query: searchQuery.trim(),
      category: selectedCategory,
      assetId,
    });
  };

  const clearFilters = () => {
    setSearchQuery("");
    setSelectedCategory("all");
    onResultsChange({
      type: "reset",
      query: "",
      category: "all",
      assetId,
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search Input */}
        <div className="flex-1 relative">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            type="text"
            placeholder="חיפוש במסמכים..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="pr-10"
            dir="rtl"
          />
        </div>

        {/* Category Filter */}
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="קטגוריה" />
          </SelectTrigger>
          <SelectContent>
            {DOCUMENT_CATEGORIES.map((category) => (
              <SelectItem key={category.value} value={category.value}>
                {category.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Search Button */}
        <Button 
          onClick={handleSearch} 
          className="w-full sm:w-auto"
        >
          חיפוש
        </Button>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-sm text-muted-foreground">סינונים פעילים:</span>
          
          {searchQuery.trim() && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <Search className="h-3 w-3" />
              &quot;{searchQuery}&quot;
              <button
                onClick={() => setSearchQuery("")}
                className="ml-1 hover:bg-muted rounded-full p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {selectedCategory && selectedCategory !== "all" && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <Filter className="h-3 w-3" />
              {selectedCategory}
              <button
                onClick={() => setSelectedCategory("all")}
                className="ml-1 hover:bg-muted rounded-full p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="text-xs h-6 px-2"
          >
            נקה הכל
          </Button>
        </div>
      )}
    </div>
  );
}
