import sqlite3

# Connect to database
conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Check current schema
print("Current users table schema:")
c.execute('PRAGMA table_info(users)')
columns = c.fetchall()
for col in columns:
    print(f"  Column {col[1]}: {col[2]}")

column_names = [col[1] for col in columns]

# Add missing columns if needed
if 'created_at' not in column_names:
    print("\nAdding 'created_at' column...")
    c.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    print("✅ Added 'created_at' column")
else:
    print("\n✅ 'created_at' column already exists")

if 'last_login' not in column_names:
    print("Adding 'last_login' column...")
    c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    print("✅ Added 'last_login' column")
else:
    print("✅ 'last_login' column already exists")

conn.commit()

# Verify final schema
print("\nFinal users table schema:")
c.execute('PRAGMA table_info(users)')
for col in c.fetchall():
    print(f"  Column {col[1]}: {col[2]}")

# Check how many users exist
c.execute('SELECT COUNT(*) FROM users')
user_count = c.fetchone()[0]
print(f"\n📊 Total users in database: {user_count}")

conn.close()
print("\n✅ Database migration complete!")
