from core.models import Asset
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create sample assets for testing the enrichment pipeline'

    def handle(self, *args, **options):
        self.stdout.write('🎯 Creating sample assets...')
        
        # Sample assets
        sample_assets = [
            {
                'scope_type': 'neighborhood',
                'city': 'תל אביב',
                'neighborhood': 'רמת החייל',
                'status': 'ready',
                'meta': {
                    'scope': {'type': 'neighborhood', 'value': 'רמת החייל', 'city': 'תל אביב'},
                    'radius': 250
                }
            },
            {
                'scope_type': 'address',
                'city': 'תל אביב',
                'street': 'הגולן',
                'number': 32,
                'status': 'ready',
                'meta': {
                    'scope': {'type': 'address', 'value': 'הגולן 32, תל אביב', 'city': 'תל אביב'},
                    'radius': 150
                }
            }
        ]
        
        created_count = 0
        for asset_data in sample_assets:
            asset, created = Asset.objects.get_or_create(
                scope_type=asset_data['scope_type'],
                city=asset_data['city'],
                defaults=asset_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'✅ Created asset: {asset}')
            else:
                self.stdout.write(f'⚠️  Asset already exists: {asset}')
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Successfully created {created_count} sample assets!')
        )
