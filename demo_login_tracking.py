from community.db import create_user, authenticate
import sqlite3
from datetime import datetime

print("=" * 80)
print("🧪 LOGIN TRACKING DEMONSTRATION")
print("=" * 80)

# Create a new test user
test_username = "demo_user_test"
test_password = "test123"

print(f"\n1️⃣ Creating new test user: {test_username}")
success = create_user(test_username, test_password, role='farmer')

if success:
    print(f"   ✅ User created successfully!")
else:
    print(f"   ℹ️  User already exists, using existing user")

# Check user data BEFORE login
print(f"\n2️⃣ Checking user data BEFORE first login:")
conn = sqlite3.connect('community/community.db')
c = conn.cursor()
c.execute('SELECT username, role, created_at, last_login FROM users WHERE username=?', (test_username,))
before = c.fetchone()

if before:
    username, role, created_at, last_login = before
    print(f"   Username: {username}")
    print(f"   Role: {role}")
    print(f"   Created At: {created_at}")
    print(f"   Last Login: {last_login or '❌ NULL (Never logged in)'}")

conn.close()

# Simulate LOGIN
print(f"\n3️⃣ Simulating user login...")
print(f"   Calling authenticate('{test_username}', '{test_password}')")

result = authenticate(test_username, test_password)

if result:
    print(f"   ✅ Login successful!")
    print(f"   Returned: {result}")
else:
    print(f"   ❌ Login failed!")

# Check user data AFTER login
print(f"\n4️⃣ Checking user data AFTER login:")
conn = sqlite3.connect('community/community.db')
c = conn.cursor()
c.execute('SELECT username, role, created_at, last_login FROM users WHERE username=?', (test_username,))
after = c.fetchone()

if after:
    username, role, created_at, last_login = after
    print(f"   Username: {username}")
    print(f"   Role: {role}")
    print(f"   Created At: {created_at}")
    print(f"   Last Login: {last_login or 'NULL'}")
    
    if last_login:
        # Calculate time ago
        login_dt = datetime.fromisoformat(last_login)
        formatted = login_dt.strftime("%b %d, %Y at %I:%M:%S %p")
        print(f"   ✅ Last Login (formatted): {formatted}")
        print(f"   🕐 This happened: Just now!")

conn.close()

print("\n" + "=" * 80)
print("🎉 DEMONSTRATION COMPLETE!")
print("=" * 80)
print("\n📋 WHAT HAPPENED:")
print("   1. Created a new user (or used existing)")
print("   2. Before login: last_login was NULL")
print("   3. Called authenticate() - this triggers login tracking")
print("   4. After login: last_login was updated to current timestamp!")
print("\n💡 NOW CHECK YOUR ADMIN PANEL:")
print(f"   1. Refresh the admin page: http://localhost:8506?admin=true")
print(f"   2. Go to 'User Management' tab")
print(f"   3. Look for user: {test_username}")
print(f"   4. You'll see 'Last Login' with the current time!")
print("\n" + "=" * 80)
