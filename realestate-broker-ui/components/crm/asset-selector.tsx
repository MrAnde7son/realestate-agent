'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { Search, MapPin, Home, X } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { apiClient } from '@/lib/api-client';
import type { Asset } from '@/lib/normalizers/asset';

interface AssetSelectorProps {
  selectedAssetId?: number;
  onAssetSelect: (asset: Asset | null) => void;
  placeholder?: string;
}

export function AssetSelector({ 
  selectedAssetId, 
  onAssetSelect, 
  placeholder = "בחר נכס" 
}: AssetSelectorProps) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [filteredAssets, setFilteredAssets] = useState<Asset[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

  // Load assets on component mount
  useEffect(() => {
    loadAssets();
  }, []);

  // Filter assets based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredAssets(assets);
    } else {
      const filtered = assets.filter(asset => 
        asset.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.city?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.neighborhood?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredAssets(filtered);
    }
  }, [searchTerm, assets]);

  // Set selected asset when selectedAssetId changes
  useEffect(() => {
    if (selectedAssetId && assets.length > 0) {
      const asset = assets.find(a => a.id === selectedAssetId);
      setSelectedAsset(asset || null);
    }
  }, [selectedAssetId, assets]);

  const loadAssets = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/api/assets');
      if (response.ok) {
        setAssets(response.data.rows || []);
        setFilteredAssets(response.data.rows || []);
      }
    } catch (error) {
      console.error('Error loading assets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssetSelect = (asset: Asset) => {
    setSelectedAsset(asset);
    onAssetSelect(asset);
    setIsOpen(false);
  };

  const handleClearSelection = () => {
    setSelectedAsset(null);
    onAssetSelect(null);
  };

  const formatAssetDisplay = (asset: Asset) => {
    const parts = [asset.address, asset.city, asset.neighborhood].filter(Boolean);
    return parts.join(', ');
  };

  const formatAssetPrice = (asset: Asset) => {
    if (!asset.price) return '';
    return new Intl.NumberFormat('he-IL').format(asset.price) + ' ₪';
  };

  return (
    <div className="space-y-2">
      <Label>נכס (אופציונלי)</Label>
      
      {selectedAsset ? (
        <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
          <div className="flex items-center gap-3">
            <Home className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">{formatAssetDisplay(selectedAsset)}</div>
              <div className="text-sm text-muted-foreground">
                {selectedAsset.rooms && `${selectedAsset.rooms} חדרים`}
                {selectedAsset.area && ` • ${selectedAsset.area} מ"ר`}
                {selectedAsset.price && ` • ${formatAssetPrice(selectedAsset)}`}
              </div>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleClearSelection}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ) : (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button 
              type="button" 
              variant="outline" 
              className="w-full justify-start text-muted-foreground"
            >
              <Search className="h-4 w-4 mr-2" />
              {placeholder}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>בחר נכס</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="חפש לפי כתובת, עיר או שכונה..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pr-10"
                />
              </div>
              
              <div className="max-h-96 overflow-y-auto space-y-2">
                {isLoading ? (
                  <div className="text-center py-4 text-muted-foreground">
                    טוען נכסים...
                  </div>
                ) : filteredAssets.length === 0 ? (
                  <div className="text-center py-4 text-muted-foreground">
                    {searchTerm ? 'לא נמצאו נכסים המתאימים לחיפוש' : 'אין נכסים זמינים'}
                  </div>
                ) : (
                  filteredAssets.map((asset) => (
                    <div
                      key={asset.id}
                      onClick={() => handleAssetSelect(asset)}
                      className="p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                          <div className="flex-1">
                            <div className="font-medium">{formatAssetDisplay(asset)}</div>
                            <div className="text-sm text-muted-foreground mt-1">
                              {asset.rooms && `${asset.rooms} חדרים`}
                              {asset.area && ` • ${asset.area} מ"ר`}
                              {asset.type && ` • ${asset.type}`}
                            </div>
                            {asset.price && (
                              <div className="text-sm font-medium text-green-600 mt-1">
                                {formatAssetPrice(asset)}
                              </div>
                            )}
                          </div>
                        </div>
                        {asset.price && (
                          <Badge variant="secondary" className="text-xs">
                            {formatAssetPrice(asset)}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
