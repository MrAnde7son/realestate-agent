# -*- coding: utf-8 -*-
"""
Ramat Gan municipal GIS client.
Uses the v5.gis-net.co.il proxy service.
"""

from typing import Dict
from gis.proxy_gis_client import ProxyGISClient


class RamatGanGIS(ProxyGISClient):
    """Client for Ramat Gan municipal GIS."""
    
    def get_service_url(self) -> str:
        return "http://arcgis006/arcgis/rest/services/RamatGan/RamatGan_maindata/MapServer"
    
    def get_referer(self) -> str:
        return "https://v5.gis-net.co.il/v5/ramat_gan"
    
    def get_cookies(self) -> Dict[str, str]:
        """Return cookies for Ramat Gan authentication.
        
        Note: These cookies may expire. In production, you may want to:
        1. Fetch them dynamically from the main page
        2. Store them in a session
        3. Use environment variables or a config file
        """
        return {
            "ASP.NET_SessionId": "svvfa4jlmzfkkmxj5ll5dlry",
            "_gid": "GA1.3.305540927.1766052238",
            "_hertzeliya": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9IUlpfUHJpbnQxL0dQU2VydmVyL0V4cG9ydCUyMFdlYiUyME1hcCIsImd1cmwiOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL1V0aWxpdGllcy9HZW9tZXRyeS9HZW9tZXRyeVNlcnZlciIsImV1cmwiOiJodHRwczovL3Y1Lmdpcy1uZXQuY28uaWwvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvSGVyemxpeWEvaGVyemxpeWFfZWRpdC9GZWF0dXJlU2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0hlcnpsaXlhL2hlcnpsaXlhX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9oZXJ6bGl5YV9tYWluX2RhdGUxL01hcFNlcnZlciIsIm1zaWRzIjoiOS0xNTciLCJuYmYiOjE3NjYwOTA0NTQsImV4cCI6MTc2NjA5NzY1NCwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.-6esXLuTasiovpXjsrI2oZ9gUIVuj8eygDSfcFcsNkU",
            "_ga_8QML5PBNRE": "GS2.1.s1766089555$o3$g1$t1766090456$j55$l0$h0",
            "_batyam": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9CYXRfeWFtL2JhdHlhbV9QcmludDEvR1BTZXJ2ZXIvRXhwb3J0JTIwV2ViJTIwTWFwIiwiZ3VybCI6Imh0dHA6Ly9hcmNnaXMwMDYvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvVXRpbGl0aWVzL0dlb21ldHJ5L0dlb21ldHJ5U2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA2L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0JhdF95YW0vYmF0eWFtX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9CYXRfeWFtL2JhdHlhbV9tYWluX2RhdGFfcHVibGljL01hcFNlcnZlciIsIm1zaWRzIjoiMC0yNiwyOC0xMzQiLCJuYmYiOjE3NjYwOTA3MjAsImV4cCI6MTc2NjA5NzkyMCwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.DNUu6uyvKcfcspIBsY5lFyOAEif-EPHYQgWFuFpNqVM",
            "_ga_DRKJ9KDWZ0": "GS2.1.s1766090557$o1$g1$t1766090721$j56$l0$h0",
            "_ga": "GA1.1.797682413.1766052238",
            "_ramat_gan": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9SYW1hdEdhbi9SYW1hdEdhblByaW50L0dQU2VydmVyL0V4cG9ydCUyMFdlYiUyME1hcCIsImd1cmwiOiJodHRwOi8vYXJjZ2lzMDA2L2FyY2dpcy9yZXN0L3NlcnZpY2VzL1V0aWxpdGllcy9HZW9tZXRyeS9HZW9tZXRyeVNlcnZlciIsIm92ZXJ2aWV3IjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9SYW1hdEdhbi9SYW1hdEdhbl9IeWJyaWQvTWFwU2VydmVyIiwibXVybCI6Imh0dHA6Ly9hcmNnaXMwMDYvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvUmFtYXRHYW4vUmFtYXRHYW5fbWFpbmRhdGEvTWFwU2VydmVyIiwibXNpZHMiOiIwLTEwNSwxMDctMjUzLDI2OC0yNzUiLCJuYmYiOjE3NjYwOTEwODMsImV4cCI6MTc2NjA5ODI4MywiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.C9s9ji07oBJgniJSrCN8sPFlPH5kH-TcHU_ur9YewQ0",
            "TS01d52e22": "01fa9750ce999128e519d35c386b254f9f79c66dcb6dda6121e247c8d471b09b35405bf7a55715a3d4f492f00b8a92a175ccf126eb7402d8f43864825c345ef68a32e396d147b22288e5f021e6457c29407d29b30b5661caba681df49cc8f5744ebd9cc60b7578e18c0bebca88ef622a4276f82f05",
            "_gat": "1",
            "_ga_3HDGMVD29Z": "GS2.1.s1766091145$o1$g1$t1766091213$j52$l0$h0",
        }
    
    def get_layer_id_for_blocks(self) -> int:
        """Layer ID for blocks (גושים) in Ramat Gan."""
        return 212  # Based on the simulation script
    
    def get_layer_id_for_parcels(self) -> int:
        """Layer ID for parcels (חלקות) in Ramat Gan.
        
        Note: This may need to be determined by inspecting the service.
        Using a placeholder value for now.
        """
        # You may need to find the correct layer ID by inspecting the service
        # For now, returning a placeholder
        return 213  # This should be verified



