import sqlite3
from datetime import datetime

conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Get users with NULL created_at or last_login
c.execute('SELECT id, username FROM users WHERE created_at IS NULL OR last_login IS NULL')
users_to_update = c.fetchall()

if users_to_update:
    print(f"Found {len(users_to_update)} users with missing timestamps")
    
    # Set a default timestamp for existing users
    default_time = datetime(2025, 1, 1, 0, 0, 0).isoformat()
    
    for user_id, username in users_to_update:
        print(f"Updating user: {username}")
        c.execute('''
            UPDATE users 
            SET created_at = COALESCE(created_at, ?),
                last_login = NULL
            WHERE id = ?
        ''', (default_time, user_id))
    
    conn.commit()
    print(f"\n✅ Updated {len(users_to_update)} users with default timestamps")
else:
    print("✅ All users already have timestamps")

# Verify
c.execute('SELECT id, username, created_at, last_login FROM users')
users = c.fetchall()
print(f"\n📊 Total users: {len(users)}")
print("\nSample user data:")
for user in users[:3]:
    print(f"  ID: {user[0]}, Username: {user[1]}, Created: {user[2]}, Last Login: {user[3]}")

conn.close()
print("\n✅ Database update complete!")
