import os
import django
from django.core.management import call_command

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

output_file = 'remote_data.json'
print(f"Dumping data to {output_file} using utf-8...")

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        call_command('dumpdata', exclude=['contenttypes', 'auth.permission'], indent=2, stdout=f)
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
