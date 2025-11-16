#!/usr/bin/env python3
"""Fix NULL user_id in token_blacklist_outstandingtoken before migration."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Disable foreign key checks temporarily (SQLite specific)
cursor.execute('PRAGMA foreign_keys = OFF')

# Check current state
cursor.execute('SELECT COUNT(*) FROM token_blacklist_outstandingtoken WHERE user_id IS NULL')
null_count = cursor.fetchone()[0]
print(f'Found {null_count} token(s) with NULL user_id')

if null_count > 0:
    # Get IDs of tokens with NULL user_id before deleting
    cursor.execute('SELECT id FROM token_blacklist_outstandingtoken WHERE user_id IS NULL')
    null_token_ids = [row[0] for row in cursor.fetchall()]
    print(f'Token IDs with NULL user_id: {null_token_ids}')
    
    # Delete orphaned BlacklistedToken records first
    if null_token_ids:
        placeholders = ','.join('?' * len(null_token_ids))
        cursor.execute(f'DELETE FROM token_blacklist_blacklistedtoken WHERE token_id IN ({placeholders})', null_token_ids)
        blacklisted_deleted = cursor.rowcount
        print(f'Deleted {blacklisted_deleted} orphaned BlacklistedToken record(s)')
    
    # Delete rows with NULL user_id
    cursor.execute('DELETE FROM token_blacklist_outstandingtoken WHERE user_id IS NULL')
    deleted = cursor.rowcount
    conn.commit()
    print(f'Deleted {deleted} row(s) with NULL user_id')
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM token_blacklist_outstandingtoken WHERE user_id IS NULL')
    remaining = cursor.fetchone()[0]
    print(f'Remaining NULL user_id tokens: {remaining}')
else:
    print('No NULL user_id tokens found')

# Check for and delete orphaned BlacklistedToken records
cursor.execute('''
    SELECT COUNT(*) FROM token_blacklist_blacklistedtoken bt 
    LEFT JOIN token_blacklist_outstandingtoken ot ON bt.token_id = ot.id 
    WHERE ot.id IS NULL
''')
orphaned_count = cursor.fetchone()[0]
print(f'Found {orphaned_count} orphaned BlacklistedToken record(s)')

if orphaned_count > 0:
    cursor.execute('''
        DELETE FROM token_blacklist_blacklistedtoken 
        WHERE token_id NOT IN (SELECT id FROM token_blacklist_outstandingtoken)
    ''')
    orphaned_deleted = cursor.rowcount
    conn.commit()
    print(f'Deleted {orphaned_deleted} orphaned BlacklistedToken record(s)')

# Re-enable foreign key checks
cursor.execute('PRAGMA foreign_keys = ON')

conn.close()
print('Done! You can now run migrations.')

