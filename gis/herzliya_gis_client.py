# -*- coding: utf-8 -*-
"""
Herzliya municipal GIS client.
Uses the v5.gis-net.co.il proxy service.
"""

from typing import Dict
from gis.proxy_gis_client import ProxyGISClient


class HerzliyaGIS(ProxyGISClient):
    """Client for Herzliya municipal GIS."""
    
    def get_service_url(self) -> str:
        return "http://arcgis005/arcgis/rest/services/Herzliya/herzliya_main_date1/MapServer"
    
    def get_referer(self) -> str:
        return "https://v5.gis-net.co.il/v5/Hertzeliya?minisite=public"
    
    def get_cookies(self) -> Dict[str, str]:
        """Return cookies for Herzliya authentication.
        
        Note: These cookies may expire. In production, you may want to:
        1. Fetch them dynamically from the main page
        2. Store them in a session
        3. Use environment variables or a config file
        """
        return {
            "ASP.NET_SessionId": "svvfa4jlmzfkkmxj5ll5dlry",
            "_gid": "GA1.3.305540927.1766052238",
            "_ga": "GA1.3.797682413.1766052238",
            "_hertzeliya": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9IUlpfUHJpbnQxL0dQU2VydmVyL0V4cG9ydCUyMFdlYiUyME1hcCIsImd1cmwiOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL1V0aWxpdGllcy9HZW9tZXRyeS9HZW9tZXRyeVNlcnZlciIsImV1cmwiOiJodHRwczovL3Y1Lmdpcy1uZXQuY28uaWwvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvSGVyemxpeWEvaGVyemxpeWFfZWRpdC9GZWF0dXJlU2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0hlcnpsaXlhL2hlcnpsaXlhX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9oZXJ6bGl5YV9tYWluX2RhdGUxL01hcFNlcnZlciIsIm1zaWRzIjoiOS0xNTciLCJuYmYiOjE3NjYwODk1NjYsImV4cCI6MTc2NjA5Njc2NiwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.3b_sz-TmV0av1EL70p6CBx9UoE1JoQVKGBfECN3UsHY",
            "TS01d52e22": "01fa9750ce963bad70090623c111e7ddbebaf6069b709dbf89c3ecc179de71e533b630850cb992a7f5780432440aa9e391077e141bc2881a8f20ded82ee858c84aa753c5c1ab4d4861ca44ed9119bb28ee25ea81a4",
            "_gat": "1",
            "_ga_8QML5PBNRE": "GS2.1.s1766089555$o3$g1$t1766090236$j48$l0$h0",
        }
    
    def get_layer_id_for_blocks(self) -> int:
        """Layer ID for blocks (גושים) in Herzliya."""
        return 24
    
    def get_layer_id_for_parcels(self) -> int:
        """Layer ID for parcels (חלקות) in Herzliya.
        
        Note: This may need to be determined by inspecting the service.
        Using a placeholder value for now.
        """
        # You may need to find the correct layer ID by inspecting the service
        # For now, returning a placeholder
        return 25  # This should be verified

