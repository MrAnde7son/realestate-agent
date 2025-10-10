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
import { apiClient } from "@/lib/api-client";

interface DocumentSearchProps {
  assetId?: number;
  onResultsChange: (results: any) => void;
  onLoadingChange: (loading: boolean) => void;
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
  onLoadingChange,
  className = "",
}: DocumentSearchProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [isSearching, setIsSearching] = useState(false);
  const [hasActiveFilters, setHasActiveFilters] = useState(false);

  // Check if there are active filters
  useEffect(() => {
    setHasActiveFilters(searchQuery.trim() !== "" || selectedCategory !== "all");
  }, [searchQuery, selectedCategory]);

  const handleSearch = async () => {
    if (!searchQuery.trim() && selectedCategory === "all") {
      // If no filters, get all documents by category
      await fetchDocumentsByCategory();
      return;
    }

    setIsSearching(true);
    onLoadingChange(true);

    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) {
        params.append("q", searchQuery.trim());
      }
      if (selectedCategory && selectedCategory !== "all") {
        params.append("category", selectedCategory);
      }
      if (assetId) {
        params.append("asset_id", assetId.toString());
      }

      const response = await apiClient.get(`/api/documents/search/?${params.toString()}`);
      
      if (response.ok) {
        onResultsChange({
          type: "search",
          data: response.data.results,
          count: response.data.count,
          query: searchQuery,
          category: selectedCategory,
        });
      } else {
        console.error("Search failed:", response.error);
        onResultsChange({ type: "error", data: [] });
      }
    } catch (error) {
      console.error("Search error:", error);
      onResultsChange({ type: "error", data: [] });
    } finally {
      setIsSearching(false);
      onLoadingChange(false);
    }
  };

  const fetchDocumentsByCategory = async () => {
    setIsSearching(true);
    onLoadingChange(true);

    try {
      const params = new URLSearchParams();
      if (assetId) {
        params.append("asset_id", assetId.toString());
      }

      const response = await apiClient.get(`/api/documents/by_category/?${params.toString()}`);
      
      if (response.ok) {
        onResultsChange({
          type: "category",
          data: response.data,
        });
      } else {
        console.error("Failed to fetch documents by category:", response.error);
        onResultsChange({ type: "error", data: [] });
      }
    } catch (error) {
      console.error("Category fetch error:", error);
      onResultsChange({ type: "error", data: [] });
    } finally {
      setIsSearching(false);
      onLoadingChange(false);
    }
  };

  const clearFilters = () => {
    setSearchQuery("");
    setSelectedCategory("all");
    fetchDocumentsByCategory();
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
          disabled={isSearching}
          className="w-full sm:w-auto"
        >
          {isSearching ? "מחפש..." : "חיפוש"}
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
