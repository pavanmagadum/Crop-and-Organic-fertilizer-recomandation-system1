import sqlite3

conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Get ALL users
c.execute('SELECT id, username, role, created_at, last_login FROM users ORDER BY id')
users = c.fetchall()

print("=" * 100)
print(f"COMPLETE USER DATABASE - Total Users: {len(users)}")
print("=" * 100)

for user_id, username, role, created_at, last_login in users:
    print(f"\nID: {user_id}")
    print(f"  Username: {username}")
    print(f"  Role: {role}")
    print(f"  created_at type: {type(created_at).__name__}, value: '{created_at}'")
    print(f"  last_login type: {type(last_login).__name__}, value: '{last_login}'")
    
    # Check if values are actually None or string 'None'
    if created_at is None:
        print(f"  ⚠️  created_at is None (NULL in database)")
    elif created_at == '':
        print(f"  ⚠️  created_at is empty string")
    else:
        print(f"  ✅ created_at has value")

conn.close()
