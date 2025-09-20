# CRM System Documentation

## Overview

The Nadlaner™ CRM system provides comprehensive client and lead management capabilities for real estate brokers and agents. The system is built with Django REST Framework on the backend and Next.js on the frontend, offering a modern, responsive interface for managing contacts, leads, and client relationships.

## Features

### Contact Management
- **Client Database**: Store and manage client contact information
- **Contact Search**: Advanced search and filtering capabilities
- **Tagging System**: Organize contacts with custom tags
- **Contact Analytics**: Track contact creation, updates, and interactions
- **Bulk Operations**: Import/export contacts, bulk updates

### Lead Management
- **Lead Tracking**: Complete lead lifecycle management
- **Status Workflow**: Standardized lead progression stages
- **Lead Notes**: Timestamped notes and activity tracking
- **Asset Association**: Link leads to specific properties
- **Lead Analytics**: Conversion tracking and performance metrics

### CRM Dashboard
- **Overview Statistics**: Total contacts, active leads, conversion rates
- **Recent Activity**: Latest contacts and lead updates
- **Performance Metrics**: Lead conversion analysis and trends
- **Quick Actions**: Fast access to common CRM operations

## Data Models

### Contact Model

The Contact model represents a client or potential client in the system.

**Fields:**
- `id`: Primary key
- `owner`: Foreign key to User (contact owner)
- `name`: Contact full name (max 200 characters)
- `phone`: Phone number (max 30 characters, optional)
- `email`: Email address (optional, unique per owner)
- `tags`: JSON field for custom tags (default: empty list)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Constraints:**
- Unique email per owner (soft constraint - only enforced if email exists)
- Owner-based access control

**Indexes:**
- `owner + name` for efficient owner-based searches
- `name` for global name searches
- `email` for email-based searches

### Lead Model

The Lead model represents a potential deal between a contact and a property asset.

**Fields:**
- `id`: Primary key
- `contact`: Foreign key to Contact
- `asset`: Foreign key to Asset (from core app)
- `status`: Lead status (choices from LeadStatus enum)
- `notes`: JSON field for timestamped notes
- `last_activity_at`: Last activity timestamp
- `created_at`: Creation timestamp

**Constraints:**
- Unique contact-asset pair (prevents duplicate leads)
- Owner-based access through contact ownership

**Indexes:**
- `status + last_activity_at` for lead pipeline queries
- `contact + asset` for relationship queries
- `status` for status-based filtering
- `last_activity_at` for activity-based sorting

### LeadStatus Enum

Standardized lead status workflow:

1. **NEW** ("חדש"): Initial lead status
2. **CONTACTED** ("יצירת קשר"): First contact made
3. **QUALIFIED** ("מועמד"): Lead qualified as potential client
4. **PROPOSAL** ("הצעה"): Proposal submitted
5. **NEGOTIATION** ("משא ומתן"): In negotiation phase
6. **CLOSED_WON** ("סגור זכה"): Deal closed successfully
7. **CLOSED_LOST** ("סגור הפסיד"): Deal closed unsuccessfully

## API Endpoints

### Contact Endpoints

#### List Contacts
```
GET /api/crm/contacts/
```
**Query Parameters:**
- `page`: Page number for pagination
- `page_size`: Number of contacts per page (max 100)
- `search`: Search term for name, email, or phone
- `tags`: Filter by tags (comma-separated)

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/crm/contacts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "יוסי כהן",
      "phone": "050-1234567",
      "email": "yossi@example.com",
      "tags": ["משקיע", "VIP"],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Contact
```
POST /api/crm/contacts/
```
**Request Body:**
```json
{
  "name": "יוסי כהן",
  "phone": "050-1234567",
  "email": "yossi@example.com",
  "tags": ["משקיע", "VIP"]
}
```

#### Update Contact
```
PATCH /api/crm/contacts/{id}/
```

#### Delete Contact
```
DELETE /api/crm/contacts/{id}/
```

### Lead Endpoints

#### List Leads
```
GET /api/crm/leads/
```
**Query Parameters:**
- `page`: Page number for pagination
- `page_size`: Number of leads per page (max 100)
- `status`: Filter by lead status
- `contact_id`: Filter by contact ID
- `asset_id`: Filter by asset ID

**Response:**
```json
{
  "count": 75,
  "next": "http://localhost:8000/api/crm/leads/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "contact": {
        "id": 1,
        "name": "יוסי כהן",
        "phone": "050-1234567",
        "email": "yossi@example.com",
        "tags": ["משקיע", "VIP"]
      },
      "asset_id": 123,
      "asset_address": "רחוב הרצל 15, תל אביב",
      "asset_price": 2500000,
      "asset_rooms": 4,
      "asset_area": 120.5,
      "status": "new",
      "notes": [
        {
          "ts": "2024-01-15T10:30:00Z",
          "text": "Initial contact made via phone"
        }
      ],
      "last_activity_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Lead
```
POST /api/crm/leads/
```
**Request Body:**
```json
{
  "contact_id": 1,
  "asset_id": 123,
  "status": "new",
  "notes": [
    {
      "ts": "2024-01-15T10:30:00Z",
      "text": "Initial contact made via phone"
    }
  ]
}
```

#### Update Lead Status
```
PATCH /api/crm/leads/{id}/status/
```
**Request Body:**
```json
{
  "status": "contacted"
}
```

#### Add Lead Note
```
POST /api/crm/leads/{id}/notes/
```
**Request Body:**
```json
{
  "text": "Client showed interest in property"
}
```

## Frontend Components

### CRM Page (`/crm`)

The main CRM interface with three tabs:

#### 1. Leads Tab
- **Lead Table**: Displays all leads with filtering and sorting
- **Lead Actions**: Update status, add notes, view details
- **Lead Creation**: Create new leads linking contacts to assets
- **Status Management**: Visual status indicators and workflow

#### 2. Contacts Tab
- **Contact Table**: Displays all contacts with search and filtering
- **Contact Actions**: Edit, delete, view contact details
- **Contact Creation**: Add new contacts with validation
- **Tag Management**: Add/remove tags from contacts

#### 3. Dashboard Tab
- **Statistics Cards**: Total contacts, active leads, conversion rates
- **Recent Activity**: Latest CRM activity feed
- **Performance Metrics**: Charts and analytics
- **Quick Actions**: Fast access to common operations

### CRM Components

#### ContactForm
- Form for creating and editing contacts
- Validation for required fields
- Tag input with autocomplete
- Phone and email format validation

#### LeadStatusBadge
- Visual status indicator for leads
- Color-coded status display
- Status change functionality

#### LeadRowActions
- Action buttons for lead operations
- Status update dropdown
- Note addition modal
- Lead deletion confirmation

## Analytics and Tracking

### Event Tracking

The CRM system includes comprehensive analytics tracking:

#### Contact Events
- `contact_created`: When a new contact is created
- `contact_updated`: When contact information is updated
- `contact_deleted`: When a contact is deleted

#### Lead Events
- `lead_created`: When a new lead is created
- `lead_updated`: When lead information is updated
- `lead_deleted`: When a lead is deleted
- `lead_status_changed`: When lead status is updated
- `lead_note_added`: When a note is added to a lead

#### CRM Events
- `crm_search`: When CRM search is performed
- `crm_export`: When data is exported
- `crm_dashboard_view`: When dashboard is viewed
- `crm_bulk_action`: When bulk operations are performed

### Analytics Functions

#### Track Event
```python
from crm.analytics import track_event

track_event('contact_created', {
    'contact_id': contact.id,
    'contact_name': contact.name,
    'tags': contact.tags
}, user_id)
```

#### Analytics Summary
```python
from crm.analytics import get_analytics_summary

summary = get_analytics_summary(user_id, days=30)
```

## Permissions and Security

### Access Control

#### Contact Permissions
- Users can only access their own contacts
- Contact creation requires authentication
- Contact updates require ownership
- Contact deletion requires ownership

#### Lead Permissions
- Users can only access leads for their contacts
- Lead creation requires contact ownership
- Lead updates require lead ownership
- Lead deletion requires lead ownership

#### API Permissions
- All CRM endpoints require authentication
- JWT token validation
- User context from authentication

### Data Validation

#### Contact Validation
- Name is required (max 200 characters)
- Email format validation
- Phone format validation
- Tags must be a list of strings

#### Lead Validation
- Contact must exist and be owned by user
- Asset must exist and be accessible
- Status must be valid LeadStatus choice
- Notes must be a list of objects with timestamp and text

## Testing

### Test Coverage

The CRM system includes comprehensive tests:

#### Model Tests
- Contact model validation
- Lead model validation
- Model relationships
- Model constraints

#### View Tests
- API endpoint functionality
- Permission enforcement
- Data validation
- Error handling

#### Serializer Tests
- Data serialization
- Data deserialization
- Validation logic
- Field handling

#### Analytics Tests
- Event tracking
- Analytics functions
- Error handling

### Running Tests

```bash
# Run all CRM tests
python -m pytest tests/crm/

# Run specific test files
python -m pytest tests/crm/test_models.py
python -m pytest tests/crm/test_views.py
python -m pytest tests/crm/test_analytics.py
```

## Configuration

### Django Settings

Add CRM app to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... other apps
    'crm',
]
```

### URL Configuration

Include CRM URLs in main URL configuration:
```python
urlpatterns = [
    # ... other patterns
    path('api/crm/', include('crm.urls')),
]
```

### Environment Variables

No additional environment variables are required for basic CRM functionality.

## Troubleshooting

### Common Issues

#### Import Errors
- Ensure CRM app is in `INSTALLED_APPS`
- Check Python path includes project root
- Verify all dependencies are installed

#### Permission Errors
- Check user authentication
- Verify contact/lead ownership
- Review permission classes

#### Data Validation Errors
- Check required fields are provided
- Verify data format (email, phone)
- Review JSON field structure (tags, notes)

#### API Errors
- Check request format
- Verify authentication headers
- Review error messages in response

### Debug Mode

Enable debug logging for CRM:
```python
LOGGING = {
    'loggers': {
        'crm': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Future Enhancements

### Planned Features
- **Advanced Analytics**: More detailed reporting and insights
- **Email Integration**: Direct email communication from CRM
- **Calendar Integration**: Meeting scheduling and reminders
- **Document Management**: File attachments for contacts and leads
- **Automation**: Automated follow-up sequences
- **Mobile App**: Native mobile CRM interface

### API Enhancements
- **Bulk Operations**: Bulk contact/lead operations
- **Advanced Filtering**: More sophisticated search and filter options
- **Export Formats**: Additional export formats (CSV, Excel, PDF)
- **Webhooks**: Real-time notifications for CRM events

---

*This documentation covers the complete CRM system implementation. For additional support or questions, please refer to the main project documentation or contact the development team.*
