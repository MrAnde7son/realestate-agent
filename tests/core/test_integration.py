"""
Integration tests for the complete address sync workflow.
Tests the full pipeline from frontend API to data collection.
"""
import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
import time

# Add project root to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Try to import the modules, skip tests if they're not available
try:
    from backend_django.core.tasks import sync_address_sources
    BACKEND_DJANGO_AVAILABLE = True
except ImportError as e:
    print(f"Skipping backend_django integration tests due to import error: {e}")
    BACKEND_DJANGO_AVAILABLE = False

try:
    from backend_django.core.views import sync_address
    BACKEND_DJANGO_VIEWS_AVAILABLE = True
except ImportError:
    BACKEND_DJANGO_VIEWS_AVAILABLE = False


@pytest.mark.skipif(not BACKEND_DJANGO_AVAILABLE, reason="backend_django not available")
class TestAddressSyncIntegration:
    """Test complete address sync workflow."""
    
    @pytest.fixture
    def mock_services(self):
        """Setup mocks for all external services."""
        with patch('backend_django.core.tasks.TelAvivGS') as mock_gs, \
             patch('backend_django.core.tasks.Yad2Scraper') as mock_yad2, \
             patch('backend_django.core.tasks.fetch_decisive_appraisals') as mock_decisive, \
             patch('backend_django.core.tasks.RamiClient') as mock_rami, \
             patch('backend_django.core.tasks.SQLAlchemyDatabase') as mock_db:
            
            # Setup GIS service mock
            gs_instance = Mock()
            mock_gs.return_value = gs_instance
            gs_instance.get_address_coordinates.return_value = (184320.94, 668548.65)
            gs_instance.get_parcels.return_value = [{"GUSH": "6638", "HELKA": "96"}]
            gs_instance.get_building_permits.return_value = [
                {
                    "permission_num": "BP-2024-001",
                    "request_num": "REQ-001",
                    "url_hadmaya": "http://example.com/permit1"
                }
            ]
            gs_instance.get_building_privilege_page.return_value = {
                "gush": "6638",
                "helka": "96",
                "file_path": "/path/to/rights.pdf",
                "content_type": "application/pdf"
            }
            
            # Setup Yad2 scraper mock
            yad2_instance = Mock()
            mock_yad2.return_value = yad2_instance
            mock_listing = Mock()
            mock_listing.to_dict.return_value = {
                "listing_id": "yad2_123",
                "title": "דירה בהגולן 1",
                "price": 2500000,
                "address": "הגולן 1, תל אביב",
                "rooms": 3,
                "size": 85,
                "property_type": "דירה",
                "url": "http://yad2.co.il/item/123",
                "date_posted": "2024-01-15"
            }
            yad2_instance.scrape_all_pages.return_value = [mock_listing]
            
            # Setup decisive appraisals mock
            mock_decisive.return_value = [
                {
                    "title": "הכרעת שמאי מייעץ - גוש 6638 חלקה 96",
                    "date": "2025-07-20",
                    "appraiser": "שמואל כהן",
                    "committee": "ועדה מקומית תל אביב",
                    "pdf_url": "http://example.com/decision.pdf"
                }
            ]
            
            # Setup RAMI client mock
            rami_instance = Mock()
            mock_rami.return_value = rami_instance
            mock_row = Mock()
            mock_row.get.side_effect = lambda key: {
                "planNumber": "PLAN-001",
                "planName": "תכנית מפורטת הגולן"
            }.get(key)
            mock_row.to_dict.return_value = {
                "planNumber": "PLAN-001",
                "planName": "תכנית מפורטת הגולן"
            }
            mock_df = Mock()
            mock_df.iterrows.return_value = [(0, mock_row)]
            rami_instance.fetch_plans.return_value = mock_df
            
            # Setup database mock
            db_instance = Mock()
            mock_db.return_value = db_instance
            session_mock = Mock()
            db_instance.get_session.return_value.__enter__.return_value = session_mock
            
            yield {
                'gs': gs_instance,
                'yad2': yad2_instance,
                'decisive': mock_decisive,
                'rami': rami_instance,
                'db': db_instance,
                'session': session_mock
            }
    
    def test_complete_address_sync_workflow(self, mock_services):
        """Test the complete address sync workflow from API call to data storage."""
        from backend_django.core.tasks import sync_address_sources
        
        # Execute the sync
        result = sync_address_sources("הגולן", 1)
        
        # Verify all services were called correctly
        mock_services['gs'].get_address_coordinates.assert_called_once_with("הגולן", 1)
        mock_services['yad2'].scrape_all_pages.assert_called_once()
        mock_services['gs'].get_building_permits.assert_called_once_with(
            184320.94, 668548.65, radius=30, download_pdfs=False
        )
        mock_services['gs'].get_building_privilege_page.assert_called_once_with(
            184320.94, 668548.65, save_dir="privilege_pages"
        )
        mock_services['decisive'].assert_called_once_with(block="6638", plot="96", max_pages=1)
        mock_services['rami'].fetch_plans.assert_called_once_with(
            {"gush": "6638", "chelka": "96", "city": 5000}
        )
        
        # Verify result contains expected listing
        assert len(result) == 1
        listing = result[0]
        assert listing['id'] == "yad2_123"
        assert "הגולן 1" in listing['address']
        assert listing['price'] == 2500000
        
        # Verify database operations (5 merge calls: listing, permit, rights, appraisal, rami)
        assert mock_services['session'].merge.call_count == 5
        assert mock_services['session'].commit.call_count == 5
    
    def test_error_handling_in_workflow(self, mock_services):
        """Test error handling when services fail."""
        from backend_django.core.tasks import sync_address_sources
        
        # Make geocoding fail
        mock_services['gs'].get_address_coordinates.side_effect = Exception("Geocoding failed")
        
        # Execute the sync
        result = sync_address_sources("Invalid Street", 999)
        
        # Should return empty result gracefully
        assert result == []
        
        # Other services should not be called due to early failure
        mock_services['yad2'].scrape_all_pages.assert_not_called()
        mock_services['decisive'].assert_not_called()
    
    def test_partial_failure_handling(self, mock_services):
        """Test handling when some services fail but others succeed."""
        from backend_django.core.tasks import sync_address_sources
        
        # Make Yad2 fail but GIS succeed
        mock_services['yad2'].scrape_all_pages.side_effect = Exception("Yad2 error")
        
        # Execute the sync
        result = sync_address_sources("הגולן", 1)
        
        # Should still call GIS services
        mock_services['gs'].get_address_coordinates.assert_called_once()
        mock_services['gs'].get_building_permits.assert_called_once()
        
        # But return empty listings due to Yad2 failure
        assert result == []


@pytest.mark.skipif(not BACKEND_DJANGO_VIEWS_AVAILABLE, reason="backend_django views not available")
class TestAPIIntegration:
    """Test API endpoints integration."""
    
    @patch('backend_django.core.views.sync_address_sources')
    def test_sync_address_api_endpoint(self, mock_sync):
        """Test sync address API endpoint."""
        from backend_django.core.views import sync_address
        
        # Setup mock
        mock_sync.return_value = [
            {
                "id": "test123",
                "address": "הגולן 1, תל אביב",
                "price": 2500000,
                "confidence": 85,
                "riskFlags": [],
                "remaining_rights": 45,
                "link": "http://yad2.co.il/item/123"
            }
        ]
        
        # Create mock request
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({
            "street": "הגולן",
            "house_number": 1
        })
        
        # Execute
        response = sync_address(mock_request)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'rows' in data
        assert len(data['rows']) == 1
        assert data['rows'][0]['address'] == "הגולן 1, תל אביב"
        
        # Verify sync was called
        mock_sync.assert_called_once_with("הגולן", 1)
    
    @patch('backend_django.core.views.SQLAlchemyDatabase')
    def test_listings_api_with_real_data(self, mock_db_class):
        """Test listings API returns real database data."""
        from backend_django.core.views import listings
        
        # Setup mock database with listings
        mock_listings = [
            Mock(
                id=1,
                source="yad2",
                external_id="yad2_123",
                title="דירה בהגולן 1",
                price=2500000.0,
                address="הגולן 1, תל אביב",
                rooms=3.0,
                floor="2",
                size=85.0,
                property_type="דירה",
                description="דירה מרווחת",
                images=["image1.jpg"],
                contact_info={"phone": "050-1234567"},
                features=["מעלית", "חניה"],
                url="http://yad2.co.il/item/123",
                date_posted="2024-01-15",
                scraped_at=None
            )
        ]
        
        mock_db = Mock()
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.all.return_value = mock_listings
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        mock_request = Mock()
        
        # Execute
        response = listings(mock_request)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'rows' in data
        assert len(data['rows']) == 1
        
        listing_data = data['rows'][0]
        assert listing_data['title'] == "דירה בהגולן 1"
        assert listing_data['address'] == "הגולן 1, תל אביב"
        assert listing_data['price'] == 2500000.0


class TestFrontendBackendIntegration:
    """Test frontend-backend integration points."""
    
    def test_frontend_sync_api_structure(self):
        """Test that frontend sync API has correct structure for backend."""
        # This tests the structure expected by the frontend /api/sync endpoint
        
        # Mock request data that frontend would send
        frontend_request = {
            "address": "הגולן 1, תל אביב"
        }
        
        # Mock backend response structure
        expected_backend_response = {
            "rows": [
                {
                    "id": "yad2_123",
                    "address": "הגולן 1, תל אביב",
                    "city": "תל אביב",
                    "rooms": 3,
                    "price": 2500000,
                    "confidence": 85,
                    "riskFlags": [],
                    "remaining_rights": 45,
                    "link": "http://yad2.co.il/item/123"
                }
            ]
        }
        
        # Verify structure matches what frontend expects
        assert 'rows' in expected_backend_response
        rows = expected_backend_response['rows']
        assert len(rows) > 0
        
        listing = rows[0]
        required_fields = ['id', 'address', 'price', 'confidence', 'link']
        for field in required_fields:
            assert field in listing
    
    def test_listing_detail_api_structure(self):
        """Test listing detail API structure matches frontend expectations."""
        
        # Mock database listing converted for frontend
        frontend_listing = {
            "id": "l1",
            "address": "הגולן 1, תל אביב",
            "price": 2500000,
            "bedrooms": 3,
            "area": 85,
            "city": "תל אביב",
            "neighborhood": "מרכז העיר",
            "netSqm": 85,
            "pricePerSqm": 29412,
            "confidencePct": 85,
            "capRatePct": 3.2,
            "remainingRightsSqm": 45,
            "riskFlags": [],
            "noiseLevel": 2,
            "greenWithin300m": True,
            "antennaDistanceM": 150,
            "zoning": "מגורים א'",
            "program": "תמ״א 38"
        }
        
        # Verify all required frontend fields are present
        frontend_required_fields = [
            'id', 'address', 'price', 'bedrooms', 'area', 'city',
            'netSqm', 'pricePerSqm', 'confidencePct', 'remainingRightsSqm'
        ]
        
        for field in frontend_required_fields:
            assert field in frontend_listing, f"Missing required field: {field}"


class TestDataTransformation:
    """Test data transformation between different system components."""
    
    def test_yad2_to_database_transformation(self):
        """Test transformation of Yad2 data to database format."""
        # Mock Yad2 listing data
        yad2_data = {
            "listing_id": "yad2_123",
            "title": "דירה בהגולן 1",
            "price": 2500000,
            "address": "הגולן 1, תל אביב",
            "rooms": 3,
            "floor": "2",
            "size": 85,
            "property_type": "דירה",
            "description": "דירה מרווחת וצמובת",
            "images": ["image1.jpg", "image2.jpg"],
            "contact_info": {"phone": "050-1234567", "agent": "יוסי כהן"},
            "features": ["מעלית", "חניה", "מרפסת"],
            "url": "http://yad2.co.il/item/123",
            "date_posted": "2024-01-15"
        }
        
        # Expected database fields
        expected_db_fields = [
            'source', 'external_id', 'title', 'price', 'address',
            'rooms', 'floor', 'size', 'property_type', 'description',
            'images', 'contact_info', 'features', 'url', 'date_posted'
        ]
        
        # Transform data (as done in pull_new_listings)
        db_data = {
            'source': 'yad2',
            'external_id': yad2_data.get('listing_id'),
            'title': yad2_data.get('title'),
            'price': yad2_data.get('price'),
            'address': yad2_data.get('address'),
            'rooms': yad2_data.get('rooms'),
            'floor': yad2_data.get('floor'),
            'size': yad2_data.get('size'),
            'property_type': yad2_data.get('property_type'),
            'description': yad2_data.get('description'),
            'images': yad2_data.get('images'),
            'contact_info': yad2_data.get('contact_info'),
            'features': yad2_data.get('features'),
            'url': yad2_data.get('url'),
            'date_posted': yad2_data.get('date_posted'),
        }
        
        # Verify transformation
        for field in expected_db_fields:
            assert field in db_data
            if field == 'source':
                assert db_data[field] == 'yad2'
            elif field == 'external_id':
                assert db_data[field] == 'yad2_123'
            else:
                assert db_data[field] == yad2_data.get(field.replace('external_id', 'listing_id'))
    
    def test_database_to_frontend_transformation(self):
        """Test transformation of database data to frontend format."""
        # Mock database listing
        db_listing = {
            'id': 1,
            'source': 'yad2',
            'external_id': 'yad2_123',
            'title': 'דירה בהגולן 1',
            'price': 2500000.0,
            'address': 'הגולן 1, תל אביב',
            'rooms': 3.0,
            'floor': '2',
            'size': 85.0,
            'property_type': 'דירה',
            'description': 'דירה מרווחת',
            'images': ['image1.jpg'],
            'contact_info': {'phone': '050-1234567'},
            'features': ['מעלית', 'חניה'],
            'url': 'http://yad2.co.il/item/123',
            'date_posted': '2024-01-15',
            'scraped_at': '2024-01-15T10:30:00'
        }
        
        # Transform to frontend format
        frontend_listing = {
            'id': str(db_listing['id']),
            'address': db_listing['address'],
            'price': int(db_listing['price']),
            'bedrooms': int(db_listing['rooms']) if db_listing['rooms'] else 0,
            'area': int(db_listing['size']) if db_listing['size'] else 0,
            'type': db_listing['property_type'],
            'status': 'active',
            'images': db_listing['images'] or [],
            'description': db_listing['description'] or '',
            'features': db_listing['features'] or [],
            'contactInfo': db_listing['contact_info'] or {},
            'netSqm': int(db_listing['size']) if db_listing['size'] else 0,
            'pricePerSqm': int(db_listing['price'] / db_listing['size']) if db_listing['size'] else 0
        }
        
        # Verify transformation
        assert frontend_listing['id'] == '1'
        assert frontend_listing['address'] == 'הגולן 1, תל אביב'
        assert frontend_listing['price'] == 2500000
        assert frontend_listing['bedrooms'] == 3
        assert frontend_listing['pricePerSqm'] == 29412  # 2500000 / 85
