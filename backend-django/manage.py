#!/usr/bin/env python
import os
import sys

# Add external modules to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
if __name__ == '__main__':
    main()
