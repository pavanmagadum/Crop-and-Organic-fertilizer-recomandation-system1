from community.db import authenticate
import sqlite3

# Test login for an existing user
print("Testing login tracking...")
print("=" * 60)

# Try to authenticate a user (this will update their last_login)
username = "pavan"  # Change this to any existing username
password = "pavan"  # You'll need the actual password

print(f"\nAttempting to login as: {username}")
print("Note: This will update the last_login timestamp if password is correct")

# Check before login
conn = sqlite3.connect('community/community.db')
c = conn.cursor()
c.execute('SELECT username, last_login FROM users WHERE username=?', (username,))
before = c.fetchone()
if before:
    print(f"\nBEFORE login:")
    print(f"  Username: {before[0]}")
    print(f"  Last Login: {before[1] or 'NULL (Never logged in)'}")

conn.close()

# Simulate login (you need the correct password)
# result = authenticate(username, password)
# if result:
#     print(f"\n✅ Login successful!")
# else:
#     print(f"\n❌ Login failed - incorrect password")

# Check after login
# conn = sqlite3.connect('community/community.db')
# c = conn.cursor()
# c.execute('SELECT username, last_login FROM users WHERE username=?', (username,))
# after = c.fetchone()
# if after:
#     print(f"\nAFTER login:")
#     print(f"  Username: {after[0]}")
#     print(f"  Last Login: {after[1]}")
# conn.close()

print("\n" + "=" * 60)
print("\n💡 TO SEE LOGIN TRACKING WORK:")
print("1. Go to http://localhost:8506 (regular page, not admin)")
print("2. Login as any existing user")
print("3. Then go back to admin panel")
print("4. You'll see their 'Last Login' updated with current time!")
print("\n" + "=" * 60)
