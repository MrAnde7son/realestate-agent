
import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from .models import Alert
import requests

# Yad2 scraper + database imports
from yad2 import Yad2Scraper, Yad2SearchParameters
from db.database import SQLAlchemyDatabase
from db.models import (
    Listing,
    BuildingPermit,
    BuildingRights,
    DecisiveAppraisal,
    RamiValuation,
)
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from rami.rami_client import RamiClient

log = logging.getLogger(__name__)

# --- helpers ---
def _parse_street_number(address: str | None) -> tuple[Optional[str], Optional[int]]:
    """Extract street name and house number from a freeform address string."""
    if not address:
        return None, None
    match = re.search(r"(.+?)\s*(\d+)", address)
    if not match:
        return None, None
    street = match.group(1).strip()
    try:
        number = int(match.group(2))
    except ValueError:
        return None, None
    return street, number

# --- Yad2 ingestion ---
def pull_new_listings(address_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Pull new listings from Yad2 and persist them.

    This function scrapes Yad2 using the configurable :class:`Yad2Scraper`.
    Retrieved listings are saved into the shared PostgreSQL database using the
    :class:`SQLAlchemyDatabase` helper and the :class:`Listing` ORM model.
    A simplified representation of each listing is returned for the alert
    matching logic.
    """

    search_params = Yad2SearchParameters(
        city=5000,  # Tel Aviv (example)
        area=1,
        topArea=2,
        property="5,33,39",
        maxPrice=10500000,
    )
    scraper = Yad2Scraper(search_params=search_params)

    try:
        scraped = scraper.scrape_all_pages(max_pages=1)
    except Exception as e:  # pragma: no cover - network errors
        log.exception("Yad2 scrape failed: %s", e)
        return []

    db = SQLAlchemyDatabase()
    db.init_db()

    results: List[Dict[str, Any]] = []
    with db.get_session() as session:
        for listing in scraped:
            data = listing.to_dict()
            # Optionally filter listings by address substring
            if address_filter and address_filter not in (data.get("address") or ""):
                continue
            db_listing = Listing(
                source="yad2",
                external_id=data.get("listing_id"),
                title=data.get("title"),
                price=data.get("price"),
                address=data.get("address"),
                rooms=data.get("rooms"),
                floor=data.get("floor"),
                size=data.get("size"),
                property_type=data.get("property_type"),
                description=data.get("description"),
                images=data.get("images"),
                contact_info=data.get("contact_info"),
                features=data.get("features"),
                url=data.get("url"),
                date_posted=data.get("date_posted"),
            )
            session.merge(db_listing)

            results.append(
                {
                    "id": data.get("listing_id"),
                    "address": data.get("address"),
                    "city": data.get("address"),
                    "rooms": data.get("rooms"),
                    "price": data.get("price"),
                    "confidence": 0,
                    "riskFlags": [],
                    "remaining_rights": 0,
                    "link": data.get("url"),
                }
            )
        session.commit()

    return results


def pull_gis_permits(x: float = 178000, y: float = 665000) -> None:
    """Fetch building permits from municipal GIS and store them."""
    gs = TelAvivGS()
    db = SQLAlchemyDatabase()
    db.init_db()
    try:
        permits = gs.get_building_permits(x, y, radius=30, download_pdfs=False)
    except Exception as e:  # pragma: no cover - network errors
        log.exception("GIS permits fetch failed: %s", e)
        return
    with db.get_session() as session:
        for p in permits:
            session.merge(
                BuildingPermit(
                    permission_num=p.get("permission_num"),
                    request_num=p.get("request_num"),
                    url=p.get("url_hadmaya"),
                    data=p,
                )
            )
        session.commit()


def pull_gis_rights(x: float = 178000, y: float = 665000) -> None:
    """Fetch building rights/privilege page from GIS and store it."""
    gs = TelAvivGS()
    db = SQLAlchemyDatabase()
    db.init_db()
    try:
        rights = gs.get_building_privilege_page(x, y, save_dir="privilege_pages")
    except Exception as e:  # pragma: no cover - network errors
        log.exception("GIS rights fetch failed: %s", e)
        return
    if not rights:
        return
    with db.get_session() as session:
        session.merge(
            BuildingRights(
                gush=rights.get("gush"),
                helka=rights.get("helka"),
                file_path=rights.get("file_path"),
                content_type=rights.get("content_type"),
                data=rights,
            )
        )
        session.commit()


def pull_decisive_appraisals(block: str = "6638", plot: str = "572") -> None:
    """Fetch decisive appraisal decisions and store them."""
    try:
        items = fetch_decisive_appraisals(block=block, plot=plot, max_pages=1)
    except Exception as e:  # pragma: no cover - network errors
        log.exception("Decisive appraisal fetch failed: %s", e)
        return
    db = SQLAlchemyDatabase()
    db.init_db()
    with db.get_session() as session:
        for item in items:
            session.merge(
                DecisiveAppraisal(
                    title=item.get("title"),
                    date=item.get("date"),
                    appraiser=item.get("appraiser"),
                    committee=item.get("committee"),
                    pdf_url=item.get("pdf_url"),
                    data=item,
                )
            )
        session.commit()


def pull_rami_valuations(params: Dict[str, Any] | None = None) -> None:
    """Fetch valuation/plan data from RAMI and store it."""
    client = RamiClient()
    search_params = params or {"PlanName": "", "CityName": "תל אביב יפו"}
    try:
        df = client.fetch_plans(search_params)
    except Exception as e:  # pragma: no cover - network errors
        log.exception("RAMI fetch failed: %s", e)
        return
    db = SQLAlchemyDatabase()
    db.init_db()
    with db.get_session() as session:
        for _, row in df.iterrows():
            session.merge(
                RamiValuation(
                    plan_number=str(row.get("planNumber") or row.get("PLAN_NUMBER")),
                    name=row.get("planName") or row.get("PLAN_NAME"),
                    data=row.to_dict(),
                )
            )
        session.commit()


def sync_address_sources(street: str, house_number: int) -> List[Dict[str, Any]]:
    """Collect data from all external sources for a specific address.
    
    Args:
        street: Street name in Hebrew
        house_number: House number as integer
        
    Returns:
        List of listings found for the address
        
    Raises:
        ValueError: If street or house_number are invalid
    """
    if not street or not street.strip():
        raise ValueError("Street name is required")
    
    if not isinstance(house_number, int) or house_number <= 0:
        raise ValueError("House number must be a positive integer")
    
    street = street.strip()
    log.info("Starting address sync for %s %d", street, house_number)
    
    gs = TelAvivGS()
    try:
        x, y = gs.get_address_coordinates(street, house_number)
        log.info("Geocoded %s %d to coordinates (%.2f, %.2f)", street, house_number, x, y)
    except Exception as e:
        log.exception("Geocode failed for %s %d: %s", street, house_number, e)
        return []

    # Collect listings with address filter
    listings = []
    try:
        listings = pull_new_listings(address_filter=f"{street} {house_number}")
        log.info("Found %d listings for %s %d", len(listings), street, house_number)
    except Exception as e:
        log.exception("Listing pull failed for %s %d: %s", street, house_number, e)
    
    # Pull GIS data with error handling
    try:
        pull_gis_permits(x, y)
        log.info("Successfully pulled GIS permits for coordinates (%.2f, %.2f)", x, y)
    except Exception as e:
        log.exception("GIS permits pull failed: %s", e)
    
    try:
        pull_gis_rights(x, y)
        log.info("Successfully pulled GIS rights for coordinates (%.2f, %.2f)", x, y)
    except Exception as e:
        log.exception("GIS rights pull failed: %s", e)

    # Get parcel data for decisive appraisals and RAMI
    block = plot = None
    try:
        parcels = gs.get_parcels(x, y)
        if parcels:
            p = parcels[0]
            block = str(p.get("GUSH") or p.get("gush") or p.get("ms_gush") or "")
            plot = str(p.get("HELKA") or p.get("helka") or p.get("ms_chelka") or "")
            log.info("Found parcel data: block=%s, plot=%s", block, plot)
        else:
            log.warning("No parcels found for coordinates (%.2f, %.2f)", x, y)
    except Exception as e:
        log.exception("Parcel lookup failed for coordinates (%.2f, %.2f): %s", x, y, e)

    # Pull parcel-dependent data if we have block and plot
    if block and plot and block != "" and plot != "":
        try:
            pull_decisive_appraisals(block, plot)
            log.info("Successfully pulled decisive appraisals for block=%s, plot=%s", block, plot)
        except Exception as e:
            log.exception("Decisive appraisals pull failed for block=%s, plot=%s: %s", block, plot, e)
        
        try:
            pull_rami_valuations({"gush": block, "chelka": plot, "city": 5000})
            log.info("Successfully pulled RAMI valuations for block=%s, plot=%s", block, plot)
        except Exception as e:
            log.exception("RAMI valuations pull failed for block=%s, plot=%s: %s", block, plot, e)
    else:
        log.warning("Skipping parcel-dependent data pulls due to missing block/plot info")

    log.info("Address sync completed for %s %d, found %d listings", street, house_number, len(listings))
    return listings


def sync_sources_for_listings() -> None:
    """Pull GIS, RAMI and appraisal data for all stored listings."""
    db = SQLAlchemyDatabase()
    db.init_db()
    gs = TelAvivGS()
    with db.get_session() as session:
        stored = session.query(Listing).all()
    for item in stored:
        street, number = _parse_street_number(item.address)
        if not (street and number):
            continue
        try:
            x, y = gs.get_address_coordinates(street, number)
        except Exception as e:  # pragma: no cover - network errors
            log.warning("Geocode failed for listing %s: %s", item.id, e)
            continue
        pull_gis_permits(x, y)
        pull_gis_rights(x, y)
        block = plot = None
        try:
            parcels = gs.get_parcels(x, y)
            if parcels:
                p = parcels[0]
                block = str(p.get("GUSH") or p.get("gush") or p.get("ms_gush"))
                plot = str(p.get("HELKA") or p.get("helka") or p.get("ms_chelka"))
        except Exception as e:  # pragma: no cover - network errors
            log.warning("Parcel lookup failed for listing %s: %s", item.id, e)
        if block and plot:
            pull_decisive_appraisals(block, plot)
            pull_rami_valuations({"gush": block, "chelka": plot, "city": 5000})


def sync_external_sources() -> List[Dict[str, Any]]:
    """Pull new listings and sync external sources for each stored listing."""
    listings = pull_new_listings()
    sync_sources_for_listings()
    return listings

def matches(criteria: Dict[str, Any], listing: Dict[str, Any]) -> bool:
    c = criteria or {}
    # city
    if c.get('city') and listing.get('city') != c['city']:
        return False
    # price cap
    if c.get('max_price') is not None and listing.get('price') is not None:
        if listing['price'] > float(c['max_price']):
            return False
    # beds range
    beds = c.get('beds') or {}
    if beds.get('min') is not None and listing.get('rooms') is not None:
        if listing['rooms'] < int(beds['min']):
            return False
    if beds.get('max') is not None and listing.get('rooms') is not None:
        if listing['rooms'] > int(beds['max']):
            return False
    # model confidence
    if c.get('confidence_min') is not None and listing.get('confidence') is not None:
        if listing['confidence'] < float(c['confidence_min']):
            return False
    # risk flags
    risk = c.get('risk')
    if risk == 'none' and listing.get('riskFlags'):
        return False
    # remaining rights
    if c.get('remaining_rights_min') is not None:
        if (listing.get('remaining_rights') or 0) < float(c['remaining_rights_min']):
            return False
    return True

def notify_email(subject: str, body: str, to_email: str) -> None:
    api_key = os.environ.get('SENDGRID_API_KEY')
    email_from = os.environ.get('EMAIL_FROM', 'noreply@example.com')
    if not (api_key and to_email):
        log.info("[EMAIL MOCK] %s -> %s\n%s", subject, to_email or '(unset)', body)
        return
    # SendGrid minimal REST call
    try:
        resp = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'personalizations': [{'to': [{'email': to_email}]}],
                'from': {'email': email_from},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': body}]
            },
            timeout=10
        )
        if resp.status_code >= 300:
            log.error('SendGrid failed: %s %s', resp.status_code, resp.text)
    except Exception as e:
        log.exception('SendGrid error: %s', e)

def notify_whatsapp(body: str, to_number: str) -> None:
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_num = os.environ.get('TWILIO_WHATSAPP_FROM')  # e.g., 'whatsapp:+14155238886'
    if not (sid and token and from_num and to_number):
        log.info("[WHATSAPP MOCK] -> %s\n%s", to_number or '(unset)', body)
        return
    url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    data = {
        'To': f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number,
        'From': from_num,
        'Body': body
    }
    try:
        resp = requests.post(url, data=data, auth=(sid, token), timeout=10)
        if resp.status_code >= 300:
            log.error('Twilio failed: %s %s', resp.status_code, resp.text)
    except Exception as e:
        log.exception('Twilio error: %s', e)

def notify(alert: Alert, listing: Dict[str, Any]) -> None:
    subject = f"התראה: פריט חדש תואם — {listing.get('address')}"
    body = (        f"נמצא נכס תואם חוק '{alert.id}'.\n"
        f"כתובת: {listing.get('address')} ({listing.get('city')})\n"
        f"חדרים: {listing.get('rooms')}\n"
        f"מחיר: {listing.get('price')}\n"
        f"Confidence: {listing.get('confidence')}\n"
        f"זכויות נותרות: {listing.get('remaining_rights')}\n"
        f"קישור: {listing.get('link')}\n"
    )
    channels = alert.notify or []
    default_email = os.environ.get('ALERT_DEFAULT_EMAIL')
    default_wa = os.environ.get('ALERT_DEFAULT_WHATSAPP_TO')
    if 'email' in channels:
        notify_email(subject, body, default_email)
    if 'whatsapp' in channels:
        notify_whatsapp(body, default_wa or '')

@shared_task(name='core.tasks.evaluate_alerts')
def evaluate_alerts():
    """Periodic task: check new listings against active alerts and notify."""
    alerts = Alert.objects.filter(active=True).order_by('-id')
    if not alerts.exists():
        log.info('No active alerts; skipping evaluation.')
        return {'processed': 0, 'matches': 0}
    listings = sync_external_sources()
    processed = 0
    matched = 0
    for listing in listings:
        for alert in alerts:
            if matches(alert.criteria, listing):
                matched += 1
                notify(alert, listing)
        processed += 1
    log.info('evaluate_alerts: processed=%s matches=%s', processed, matched)
    return {'processed': processed, 'matches': matched}
