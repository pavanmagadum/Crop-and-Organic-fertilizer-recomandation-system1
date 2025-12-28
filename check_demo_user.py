import sqlite3

conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Check the demo user
c.execute('SELECT username, created_at, last_login FROM users WHERE username=?', ('demo_user_test',))
result = c.fetchone()

if result:
    print("✅ DEMO USER FOUND!")
    print(f"Username: {result[0]}")
    print(f"Created At: {result[1]}")
    print(f"Last Login: {result[2]}")
    
    if result[2]:
        print("\n🎉 SUCCESS! Login tracking is working!")
        print(f"The user's last login was recorded: {result[2]}")
    else:
        print("\n⚠️ Last login is NULL - user hasn't logged in yet")
else:
    print("❌ Demo user not found")

conn.close()
