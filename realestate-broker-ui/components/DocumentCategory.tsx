"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/Badge";
import { FileText, Download, ExternalLink, Calendar, User } from "lucide-react";
import { format } from "date-fns";
import { he } from "date-fns/locale";

interface Document {
  id: number;
  title: string;
  description?: string;
  document_type: string;
  status: string;
  filename: string;
  file_url: string;
  external_url?: string;
  external_id?: string;
  source: string;
  document_date?: string;
  uploaded_at: string;
  uploaded_by?: string;
  is_downloadable: boolean;
}

interface DocumentCategoryProps {
  category: string;
  documents: Document[];
  onDocumentClick?: (document: Document) => void;
  className?: string;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case "approved":
      return "bg-green-100 text-green-800";
    case "pending":
      return "bg-yellow-100 text-yellow-800";
    case "rejected":
      return "bg-red-100 text-red-800";
    case "expired":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    approved: "אושר",
    pending: "ממתין",
    rejected: "נדחה",
    expired: "פג תוקף",
  };
  return statusMap[status] || status;
};

const translateSource = (source: string) => {
  const translations: Record<string, string> = {
    user_upload: "העלאה ידנית",
    GIS: "מערכת מידע גיאוגרפית",
    gis_permit: "מערכת מידע גיאוגרפית",
    gis_rights: "מערכת מידע גיאוגרפית",
    RAMI: "רמ״י",
    rami_plan: "רמ״י",
    Mavat: "מבת",
    Gov: "ממשלתי",
    tabu: "טאבו",
    tabu_upload: "טאבו",
    meta_migration: "העברה מנתונים קיימים",
    yad2: "יד2",
    nadlan: "נדלן",
    pipeline: "צינור נתונים",
    external: "מקור חיצוני",
  };
  return translations[source] || source;
};

export default function DocumentCategory({
  category,
  documents,
  onDocumentClick,
  className = "",
}: DocumentCategoryProps) {
  if (documents.length === 0) {
    return null;
  }

  const handleDocumentClick = (document: Document) => {
    if (onDocumentClick) {
      onDocumentClick(document);
    }
  };

  const handleDownload = (e: React.MouseEvent, document: Document) => {
    e.stopPropagation();
    if (document.is_downloadable && document.file_url) {
      window.open(document.file_url, "_blank");
    }
  };

  const handleExternalLink = (e: React.MouseEvent, document: Document) => {
    e.stopPropagation();
    if (document.external_url) {
      window.open(document.external_url, "_blank");
    }
  };

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <FileText className="h-5 w-5" />
          {category}
          <Badge variant="secondary" className="text-xs">
            {documents.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {documents.map((document) => (
          <div
            key={document.id}
            className="flex items-start justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
            onClick={() => handleDocumentClick(document)}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-2 mb-2">
                <h4 className="font-medium text-sm leading-tight">
                  {document.title || document.filename}
                </h4>
                <Badge
                  variant="outline"
                  className={`text-xs ${getStatusColor(document.status)}`}
                >
                  {getStatusLabel(document.status)}
                </Badge>
              </div>
              
              {document.description && (
                <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                  {document.description}
                </p>
              )}
              
              <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                {document.document_type && (
                  <span>סוג: {document.document_type}</span>
                )}
                {document.source && (
                  <span>מקור: {translateSource(document.source)}</span>
                )}
                {document.external_id && (
                  <span>מזהה: {document.external_id}</span>
                )}
                {document.document_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {format(new Date(document.document_date), "dd/MM/yyyy", {
                      locale: he,
                    })}
                  </span>
                )}
                {document.uploaded_by && (
                  <span className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {document.uploaded_by}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-1 ml-3">
              {document.is_downloadable && document.file_url && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => handleDownload(e, document)}
                  className="h-8 w-8 p-0"
                  title="הורד"
                >
                  <Download className="h-4 w-4" />
                </Button>
              )}
              
              {document.external_url && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => handleExternalLink(e, document)}
                  className="h-8 w-8 p-0"
                  title="פתח בקישור חיצוני"
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
