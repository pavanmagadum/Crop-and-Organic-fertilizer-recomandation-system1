import sqlite3
from datetime import datetime

conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Set a reasonable default timestamp for existing users
default_time = datetime(2024, 12, 1, 10, 0, 0).isoformat()

print("Updating all users with NULL created_at...")

# Update users with NULL created_at
c.execute('''
    UPDATE users 
    SET created_at = ?
    WHERE created_at IS NULL
''', (default_time,))

rows_updated = c.rowcount
conn.commit()

print(f"✅ Updated {rows_updated} users with default registration date")

# Verify the update
c.execute('SELECT id, username, created_at, last_login FROM users ORDER BY id DESC')
users = c.fetchall()

print(f"\n📊 Total users: {len(users)}")
print("\nAll users now have timestamps:")
for user in users:
    user_id, username, created_at, last_login = user
    print(f"  {username:20} | Registered: {created_at:25} | Last Login: {last_login or 'Never'}")

conn.close()
print("\n✅ All users now have proper timestamps!")
