import sqlite3
from datetime import datetime

conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Get all users and show their current status
c.execute('SELECT id, username, role, created_at, last_login FROM users ORDER BY id DESC LIMIT 5')
users = c.fetchall()

print("=" * 80)
print("CURRENT USER STATUS (Top 5 users)")
print("=" * 80)

for user_id, username, role, created_at, last_login in users:
    print(f"\n👤 User: {username}")
    print(f"   ID: {user_id}")
    print(f"   Role: {role}")
    
    if created_at:
        try:
            created_dt = datetime.fromisoformat(created_at)
            created_display = created_dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            created_display = created_at
    else:
        created_display = "N/A"
    
    print(f"   📅 Registered: {created_display}")
    
    if last_login:
        try:
            login_dt = datetime.fromisoformat(last_login)
            last_login_display = login_dt.strftime("%b %d, %Y at %I:%M %p")
            
            # Calculate time since last login
            time_diff = datetime.now() - login_dt
            if time_diff.days == 0:
                if time_diff.seconds < 3600:
                    time_ago = f"{time_diff.seconds // 60} minutes ago"
                else:
                    time_ago = f"{time_diff.seconds // 3600} hours ago"
            elif time_diff.days == 1:
                time_ago = "Yesterday"
            else:
                time_ago = f"{time_diff.days} days ago"
            
            print(f"   🕐 Last Login: {last_login_display} ({time_ago})")
        except:
            print(f"   🕐 Last Login: {last_login}")
    else:
        print(f"   🕐 Last Login: Never logged in")

print("\n" + "=" * 80)

# Count statistics
c.execute('SELECT COUNT(*) FROM users WHERE last_login IS NOT NULL')
logged_in_count = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM users')
total_count = c.fetchone()[0]

print(f"\n📊 STATISTICS:")
print(f"   Total Users: {total_count}")
print(f"   Users who have logged in: {logged_in_count}")
print(f"   Users who never logged in: {total_count - logged_in_count}")

conn.close()
