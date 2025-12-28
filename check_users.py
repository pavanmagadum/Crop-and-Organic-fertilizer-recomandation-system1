import sqlite3

conn = sqlite3.connect('community/community.db')
c = conn.cursor()

# Test the exact query used in get_all_users
c.execute('SELECT id, username, role, created_at, last_login FROM users ORDER BY id DESC')
rows = c.fetchall()

print(f"Total users: {len(rows)}")
print("\nUser data structure:")
for i, row in enumerate(rows):
    print(f"\nUser {i+1}:")
    print(f"  Length: {len(row)}")
    print(f"  Data: {row}")
    print(f"  Types: {[type(x).__name__ for x in row]}")

conn.close()
