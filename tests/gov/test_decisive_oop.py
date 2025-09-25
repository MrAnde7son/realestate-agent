"""Tests for the OOP decisive appraisal implementation."""

import json
from unittest import mock
from typing import Dict, List

import pytest
import requests

from gov.decisive import (
    DecisiveAppraisal, 
    DecisiveAppraisalClient, 
    APIDecisiveAppraisalParser
)


class TestDecisiveAppraisal:
    """Test the DecisiveAppraisal dataclass."""
    
    def test_create_appraisal(self):
        """Test creating a DecisiveAppraisal object."""
        appraisal = DecisiveAppraisal(
            title="Test Title",
            date="01.01.2024",
            appraiser="Test Appraiser",
            committee="Test Committee",
            pdf_url="https://example.com/test.pdf"
        )
        
        assert appraisal.title == "Test Title"
        assert appraisal.date == "01.01.2024"
        assert appraisal.appraiser == "Test Appraiser"
        assert appraisal.committee == "Test Committee"
        assert appraisal.pdf_url == "https://example.com/test.pdf"
    
    def test_to_dict(self):
        """Test converting appraisal to dictionary."""
        appraisal = DecisiveAppraisal(
            title="Test Title",
            date="01.01.2024",
            appraiser="Test Appraiser",
            committee="Test Committee",
            pdf_url="https://example.com/test.pdf",
            appraisal_type="היטל השבחה",
            block="123",
            plot="456"
        )
        
        result = appraisal.to_dict()
        
        assert isinstance(result, dict)
        assert result["title"] == "Test Title"
        assert result["date"] == "01.01.2024"
        assert result["appraiser"] == "Test Appraiser"
        assert result["committee"] == "Test Committee"
        assert result["pdf_url"] == "https://example.com/test.pdf"
        assert result["appraisal_type"] == "היטל השבחה"
        assert result["block"] == "123"
        assert result["plot"] == "456"
    
    def test_get_pdf_urls_single(self):
        """Test get_pdf_urls with single URL."""
        appraisal = DecisiveAppraisal(
            title="Test Title",
            date="01.01.2024",
            appraiser="Test Appraiser",
            committee="Test Committee",
            pdf_url="https://example.com/test.pdf"
        )
        
        urls = appraisal.get_pdf_urls()
        assert urls == ["https://example.com/test.pdf"]
    
    def test_get_pdf_urls_multiple(self):
        """Test get_pdf_urls with multiple URLs."""
        appraisal = DecisiveAppraisal(
            title="Test Title",
            date="01.01.2024",
            appraiser="Test Appraiser",
            committee="Test Committee",
            pdf_url="https://example.com/doc1.pdf; https://example.com/doc2.pdf; https://example.com/doc3.pdf"
        )
        
        urls = appraisal.get_pdf_urls()
        expected = [
            "https://example.com/doc1.pdf",
            "https://example.com/doc2.pdf", 
            "https://example.com/doc3.pdf"
        ]
        assert urls == expected
    
    def test_get_pdf_urls_empty(self):
        """Test get_pdf_urls with empty URL."""
        appraisal = DecisiveAppraisal(
            title="Test Title",
            date="01.01.2024",
            appraiser="Test Appraiser",
            committee="Test Committee",
            pdf_url=""
        )
        
        urls = appraisal.get_pdf_urls()
        assert urls == []


class TestAPIDecisiveAppraisalParser:
    """Test the API parser."""
    
    def test_parse_empty_response(self):
        """Test parsing empty response."""
        parser = APIDecisiveAppraisalParser()
        result = parser.parse({})
        assert result == []
    
    def test_parse_no_results(self):
        """Test parsing response with no results."""
        parser = APIDecisiveAppraisalParser()
        response_data = {"Status": "OK", "TotalResults": 0}
        result = parser.parse(response_data)
        assert result == []
    
    def test_parse_single_result(self):
        """Test parsing single result."""
        parser = APIDecisiveAppraisalParser()
        response_data = {
            "Results": [
                {
                    "Data": {
                        "AppraisalHeader": "Test Appraisal",
                        "DecisiveAppraiser": "Test Appraiser",
                        "Committee": "Test Committee",
                        "DecisionDate": "2024-01-01T00:00:00+03:00",
                        "Document": [
                            {
                                "FileName": "https://example.com/test.pdf",
                                "DisplayName": "Test Document",
                                "Extension": "pdf"
                            }
                        ],
                        "AppraisalType": "היטל השבחה",
                        "Block": "123",
                        "Plot": "456"
                    }
                }
            ]
        }
        
        result = parser.parse(response_data)
        
        assert len(result) == 1
        appraisal = result[0]
        assert isinstance(appraisal, DecisiveAppraisal)
        assert appraisal.title == "Test Appraisal"
        assert appraisal.appraiser == "Test Appraiser"
        assert appraisal.committee == "Test Committee"
        assert appraisal.date == "01.01.2024"
        assert appraisal.pdf_url == "https://example.com/test.pdf"
        assert appraisal.appraisal_type == "היטל השבחה"
        assert appraisal.block == "123"
        assert appraisal.plot == "456"
    
    def test_parse_multiple_documents(self):
        """Test parsing result with multiple documents."""
        parser = APIDecisiveAppraisalParser()
        response_data = {
            "Results": [
                {
                    "Data": {
                        "AppraisalHeader": "Test Appraisal Multiple Docs",
                        "DecisiveAppraiser": "Test Appraiser",
                        "Committee": "Test Committee",
                        "DecisionDate": "2024-01-01T00:00:00+03:00",
                        "Document": [
                            {
                                "FileName": "https://example.com/doc1.pdf",
                                "DisplayName": "Document 1",
                                "Extension": "pdf"
                            },
                            {
                                "FileName": "https://example.com/doc2.pdf",
                                "DisplayName": "Document 2",
                                "Extension": "pdf"
                            },
                            {
                                "FileName": "https://example.com/doc3.pdf",
                                "DisplayName": "Document 3",
                                "Extension": "pdf"
                            }
                        ],
                        "AppraisalType": "היטל השבחה",
                        "Block": "123",
                        "Plot": "456"
                    }
                }
            ]
        }
        
        result = parser.parse(response_data)
        
        assert len(result) == 1
        appraisal = result[0]
        assert isinstance(appraisal, DecisiveAppraisal)
        assert appraisal.title == "Test Appraisal Multiple Docs"
        
        # Test combined URL
        expected_combined = "https://example.com/doc1.pdf; https://example.com/doc2.pdf; https://example.com/doc3.pdf"
        assert appraisal.pdf_url == expected_combined
        
        # Test individual URLs
        individual_urls = appraisal.get_pdf_urls()
        expected_urls = [
            "https://example.com/doc1.pdf",
            "https://example.com/doc2.pdf",
            "https://example.com/doc3.pdf"
        ]
        assert individual_urls == expected_urls
    
    def test_format_date(self):
        """Test date formatting."""
        parser = APIDecisiveAppraisalParser()
        
        # Test valid ISO date
        result = parser._format_date("2024-01-01T00:00:00+03:00")
        assert result == "01.01.2024"
        
        # Test empty date
        result = parser._format_date("")
        assert result == ""
        
        # Test invalid date
        result = parser._format_date("invalid-date")
        assert result == ""


class TestDecisiveAppraisalClient:
    """Test the DecisiveAppraisalClient."""
    
    def test_init_with_default_parser(self):
        """Test initialization with default parser."""
        client = DecisiveAppraisalClient()
        assert isinstance(client.parser, APIDecisiveAppraisalParser)
        assert client.timeout == 10  # DEFAULT_TIMEOUT
    
    def test_init_with_custom_parser(self):
        """Test initialization with custom parser."""
        custom_parser = APIDecisiveAppraisalParser()
        client = DecisiveAppraisalClient(parser=custom_parser, timeout=30)
        assert client.parser is custom_parser
        assert client.timeout == 30
    
    @mock.patch('requests.post')
    def test_fetch_appraisals_success(self, mock_post):
        """Test successful fetch of appraisals."""
        # Mock response
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "Results": [
                {
                    "Data": {
                        "AppraisalHeader": "Test Appraisal",
                        "DecisiveAppraiser": "Test Appraiser",
                        "Committee": "Test Committee",
                        "DecisionDate": "2024-01-01T00:00:00+03:00",
                        "Document": [
                            {
                                "FileName": "https://example.com/test.pdf",
                                "DisplayName": "Test Document",
                                "Extension": "pdf"
                            }
                        ],
                        "AppraisalType": "היטל השבחה",
                        "Block": "123",
                        "Plot": "456"
                    }
                }
            ],
            "TotalResults": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = DecisiveAppraisalClient()
        result = client.fetch_appraisals(block="123", plot="456", max_pages=1)
        
        assert len(result) == 1
        assert isinstance(result[0], DecisiveAppraisal)
        assert result[0].title == "Test Appraisal"
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        assert call_args.kwargs["json"]["Block"] == "123"
        assert call_args.kwargs["json"]["Plot"] == "456"
        assert call_args.kwargs["json"]["skip"] == 0
    
    @mock.patch('requests.post')
    def test_fetch_appraisals_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        client = DecisiveAppraisalClient()
        result = client.fetch_appraisals(block="123", plot="456")
        
        assert result == []
    
    @mock.patch('requests.post')
    def test_fetch_appraisals_json_error(self, mock_post):
        """Test handling of JSON parsing errors."""
        mock_response = mock.Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = DecisiveAppraisalClient()
        result = client.fetch_appraisals(block="123", plot="456")
        
        assert result == []


class TestBackwardCompatibility:
    """Test backward compatibility function."""
    
    @mock.patch('gov.decisive.DecisiveAppraisalClient')
    def test_fetch_decisive_appraisals_function(self, mock_client_class):
        """Test the backward compatibility function."""
        # Mock the client and its method
        mock_client = mock.Mock()
        mock_appraisal = DecisiveAppraisal(
            title="Test Title",
            date="01.01.2024",
            appraiser="Test Appraiser",
            committee="Test Committee",
            pdf_url="https://example.com/test.pdf"
        )
        mock_client.fetch_appraisals.return_value = [mock_appraisal]
        mock_client_class.return_value = mock_client
        
        result = DecisiveAppraisalClient().fetch_appraisals(block="123", plot="456")
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["title"] == "Test Title"
        assert result[0]["date"] == "01.01.2024"
        assert result[0]["appraiser"] == "Test Appraiser"
        assert result[0]["committee"] == "Test Committee"
        assert result[0]["pdf_url"] == "https://example.com/test.pdf"
        
        # Verify the client was used correctly
        mock_client.fetch_appraisals.assert_called_once_with(block="123", plot="456", max_pages=1)
