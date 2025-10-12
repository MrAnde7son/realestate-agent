"""
Django management command to backfill global source tables.

This command promotes existing per-asset data to global tables and creates links.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import hashlib
import json
import logging

from core.models import (
    Asset, RealEstateTransaction, SourceRecord,
    RealEstateTransactionGlobal, MavatPlanGlobal, RamiParcelGlobal,
    DecisiveRecordGlobal, Yad2ListingGlobal,
    AssetToDeal, AssetToMavatPlan, AssetToRamiParcel,
    AssetToDecisiveRecord, AssetToYad2Listing
)

logger = logging.getLogger(__name__)


def compute_key_fingerprint(key_dict):
    """Compute a stable fingerprint from cadastral identifiers."""
    normalized = {}
    for key in sorted(key_dict.keys()):
        value = key_dict[key]
        if value is not None:
            normalized[key] = str(value).strip()
    
    key_json = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(key_json.encode('utf-8')).hexdigest()


def build_key_dict_from_asset(asset):
    """Build key dictionary from an Asset instance."""
    return {
        'block': asset.block,
        'parcel': asset.parcel,
        'subparcel': asset.subparcel,
        'city': asset.city,
        'street': asset.street,
        'number': asset.number,
    }


class Command(BaseCommand):
    help = 'Backfill global source tables with existing per-asset data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch',
        )
        parser.add_argument(
            '--source',
            choices=['transactions', 'source_records', 'all'],
            default='all',
            help='Which source to backfill',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        source = options['source']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        try:
            if source in ['transactions', 'all']:
                self.backfill_transactions(dry_run, batch_size)
            
            if source in ['source_records', 'all']:
                self.backfill_source_records(dry_run, batch_size)
                
        except Exception as e:
            raise CommandError(f'Backfill failed: {e}')

    def backfill_transactions(self, dry_run, batch_size):
        """Backfill transactions to global table."""
        self.stdout.write('Processing transactions...')
        
        transactions = RealEstateTransaction.objects.select_related('asset').all()
        total_count = transactions.count()
        
        if total_count == 0:
            self.stdout.write('No transactions found to backfill')
            return
        
        promoted_count = 0
        linked_count = 0
        error_count = 0
        
        for i in range(0, total_count, batch_size):
            batch = transactions[i:i + batch_size]
            
            if not dry_run:
                with transaction.atomic():
                    for transaction in batch:
                        try:
                            result = self._promote_transaction(transaction)
                            if result['promoted']:
                                promoted_count += 1
                            if result['linked']:
                                linked_count += 1
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error promoting transaction {transaction.id}: {e}")
            else:
                # Dry run - just count what would be processed
                for transaction in batch:
                    try:
                        # Check if already exists
                        key_dict = build_key_dict_from_asset(transaction.asset)
                        key_fp = compute_key_fingerprint(key_dict)
                        
                        if transaction.deal_id:
                            external_id = str(transaction.deal_id)
                        else:
                            content = {
                                'date': transaction.date.isoformat() if transaction.date else None,
                                'price': transaction.price,
                                'address': transaction.address,
                                'key_dict': key_dict,
                            }
                            content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
                            external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
                        
                        exists = RealEstateTransactionGlobal.objects.filter(deal_id=external_id).exists()
                        if not exists:
                            promoted_count += 1
                        
                        link_exists = AssetToDeal.objects.filter(
                            asset=transaction.asset,
                            transaction__deal_id=external_id
                        ).exists()
                        if not link_exists:
                            linked_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error in dry run for transaction {transaction.id}: {e}")
            
            self.stdout.write(f'Processed {min(i + batch_size, total_count)}/{total_count} transactions')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Transactions backfill complete: {promoted_count} promoted, '
                f'{linked_count} linked, {error_count} errors'
            )
        )

    def backfill_source_records(self, dry_run, batch_size):
        """Backfill source records to global tables."""
        self.stdout.write('Processing source records...')
        
        source_records = SourceRecord.objects.select_related('asset').all()
        total_count = source_records.count()
        
        if total_count == 0:
            self.stdout.write('No source records found to backfill')
            return
        
        promoted_counts = {'mavat': 0, 'rami': 0, 'decisive': 0, 'yad2': 0}
        linked_counts = {'mavat': 0, 'rami': 0, 'decisive': 0, 'yad2': 0}
        error_count = 0
        
        for i in range(0, total_count, batch_size):
            batch = source_records[i:i + batch_size]
            
            if not dry_run:
                with transaction.atomic():
                    for record in batch:
                        try:
                            result = self._promote_source_record(record)
                            source_type = result['source_type']
                            if result['promoted']:
                                promoted_counts[source_type] += 1
                            if result['linked']:
                                linked_counts[source_type] += 1
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error promoting source record {record.id}: {e}")
            else:
                # Dry run - just count what would be processed
                for record in batch:
                    try:
                        result = self._check_source_record_exists(record)
                        source_type = result['source_type']
                        if result['promoted']:
                            promoted_counts[source_type] += 1
                        if result['linked']:
                            linked_counts[source_type] += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error in dry run for source record {record.id}: {e}")
            
            self.stdout.write(f'Processed {min(i + batch_size, total_count)}/{total_count} source records')
        
        for source_type, count in promoted_counts.items():
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{source_type.title()} records: {count} promoted, '
                        f'{linked_counts[source_type]} linked'
                    )
                )
        
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Source records backfill complete with {error_count} errors')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Source records backfill complete')
            )

    def _promote_transaction(self, transaction):
        """Promote a single transaction to global table."""
        # Build key dictionary from asset
        key_dict = build_key_dict_from_asset(transaction.asset)
        key_fp = compute_key_fingerprint(key_dict)
        
        # Build external ID (prefer deal_id, fallback to content hash)
        if transaction.deal_id:
            external_id = str(transaction.deal_id)
        else:
            content = {
                'date': transaction.date.isoformat() if transaction.date else None,
                'price': transaction.price,
                'address': transaction.address,
                'key_dict': key_dict,
            }
            content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
            external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
        
        # Create or update global transaction
        global_transaction, created = RealEstateTransactionGlobal.objects.update_or_create(
            deal_id=external_id,
            defaults={
                'key_fp': key_fp,
                'key_json': key_dict,
                'date': transaction.date,
                'price': transaction.price,
                'rooms': transaction.rooms,
                'area': transaction.area,
                'floor': transaction.floor,
                'address': transaction.address,
                'raw': transaction.raw,
                'ttl_expires_at': timezone.now() + timedelta(days=30),
            }
        )
        
        # Create link
        link, link_created = AssetToDeal.objects.get_or_create(
            asset=transaction.asset,
            transaction=global_transaction
        )
        
        return {'promoted': created, 'linked': link_created}

    def _promote_source_record(self, record):
        """Promote a single source record to global table."""
        # Build key dictionary from asset
        key_dict = build_key_dict_from_asset(record.asset)
        key_fp = compute_key_fingerprint(key_dict)
        
        if record.source == 'mavat':
            # Promote MAVAT plan
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            global_plan, created = MavatPlanGlobal.objects.update_or_create(
                plan_id=external_id,
                defaults={
                    'key_fp': key_fp,
                    'key_json': key_dict,
                    'plan_number': record.raw.get('plan_number'),
                    'plan_title': record.raw.get('plan_title'),
                    'status': record.raw.get('status'),
                    'effective_date': record.raw.get('effective_date'),
                    'plan_type': record.raw.get('plan_type'),
                    'raw': record.raw,
                    'ttl_expires_at': timezone.now() + timedelta(days=7),
                }
            )
            
            link, link_created = AssetToMavatPlan.objects.get_or_create(
                asset=record.asset,
                plan=global_plan
            )
            
            return {'source_type': 'mavat', 'promoted': created, 'linked': link_created}
            
        elif record.source in ['rami_plan', 'gov_rami']:
            # Promote RAMI parcel
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            global_parcel, created = RamiParcelGlobal.objects.update_or_create(
                rami_id=external_id,
                defaults={
                    'key_fp': key_fp,
                    'key_json': key_dict,
                    'plan_number': record.raw.get('plan_number'),
                    'plan_name': record.raw.get('plan_name'),
                    'status': record.raw.get('status'),
                    'status_date': record.raw.get('status_date'),
                    'market_value': record.raw.get('market_value'),
                    'building_rights': record.raw.get('building_rights'),
                    'raw': record.raw,
                    'ttl_expires_at': timezone.now() + timedelta(days=7),
                }
            )
            
            link, link_created = AssetToRamiParcel.objects.get_or_create(
                asset=record.asset,
                parcel=global_parcel
            )
            
            return {'source_type': 'rami', 'promoted': created, 'linked': link_created}
            
        elif record.source in ['decisive', 'appraisal_decisive']:
            # Promote decisive record
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            global_record, created = DecisiveRecordGlobal.objects.update_or_create(
                decisive_id=external_id,
                defaults={
                    'key_fp': key_fp,
                    'key_json': key_dict,
                    'appraiser': record.raw.get('appraiser'),
                    'date': record.raw.get('date'),
                    'appraised_value': record.raw.get('appraised_value'),
                    'url': record.url,
                    'raw': record.raw,
                    'ttl_expires_at': timezone.now() + timedelta(days=7),
                }
            )
            
            link, link_created = AssetToDecisiveRecord.objects.get_or_create(
                asset=record.asset,
                record=global_record
            )
            
            return {'source_type': 'decisive', 'promoted': created, 'linked': link_created}
            
        elif record.source == 'yad2':
            # Promote Yad2 listing
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            global_listing, created = Yad2ListingGlobal.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'key_fp': key_fp,
                    'key_json': key_dict,
                    'title': record.raw.get('title'),
                    'price': record.raw.get('price'),
                    'address': record.raw.get('address'),
                    'rooms': record.raw.get('rooms'),
                    'area': record.raw.get('area'),
                    'property_type': record.raw.get('property_type'),
                    'url': record.url,
                    'raw': record.raw,
                    'ttl_expires_at': timezone.now() + timedelta(days=1),
                }
            )
            
            link, link_created = AssetToYad2Listing.objects.get_or_create(
                asset=record.asset,
                listing=global_listing
            )
            
            return {'source_type': 'yad2', 'promoted': created, 'linked': link_created}
        
        return {'source_type': 'unknown', 'promoted': False, 'linked': False}

    def _check_source_record_exists(self, record):
        """Check if a source record would be promoted (dry run)."""
        key_dict = build_key_dict_from_asset(record.asset)
        
        if record.source == 'mavat':
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            exists = MavatPlanGlobal.objects.filter(plan_id=external_id).exists()
            link_exists = AssetToMavatPlan.objects.filter(
                asset=record.asset,
                plan__plan_id=external_id
            ).exists()
            
            return {'source_type': 'mavat', 'promoted': not exists, 'linked': not link_exists}
            
        elif record.source in ['rami_plan', 'gov_rami']:
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            exists = RamiParcelGlobal.objects.filter(rami_id=external_id).exists()
            link_exists = AssetToRamiParcel.objects.filter(
                asset=record.asset,
                parcel__rami_id=external_id
            ).exists()
            
            return {'source_type': 'rami', 'promoted': not exists, 'linked': not link_exists}
            
        elif record.source in ['decisive', 'appraisal_decisive']:
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            exists = DecisiveRecordGlobal.objects.filter(decisive_id=external_id).exists()
            link_exists = AssetToDecisiveRecord.objects.filter(
                asset=record.asset,
                record__decisive_id=external_id
            ).exists()
            
            return {'source_type': 'decisive', 'promoted': not exists, 'linked': not link_exists}
            
        elif record.source == 'yad2':
            external_id = record.external_id or hashlib.sha256(
                json.dumps(record.raw, sort_keys=True).encode('utf-8')
            ).hexdigest()[:32]
            
            exists = Yad2ListingGlobal.objects.filter(external_id=external_id).exists()
            link_exists = AssetToYad2Listing.objects.filter(
                asset=record.asset,
                listing__external_id=external_id
            ).exists()
            
            return {'source_type': 'yad2', 'promoted': not exists, 'linked': not link_exists}
        
        return {'source_type': 'unknown', 'promoted': False, 'linked': False}
