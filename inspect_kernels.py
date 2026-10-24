import sqlite3

db_path = "samples/collective_lens_capture.sqlite"
con = sqlite3.connect(db_path)

print("KERNEL TABLE COLUMNS")
for row in con.execute("PRAGMA table_info(CUPTI_ACTIVITY_KIND_KERNEL)"):
    print(row)

print("\nSAMPLE KERNEL RECORDS")
cur = con.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL LIMIT 5")

columns = [item[0] for item in cur.description]
print("Columns:", columns)

for record in cur.fetchall():
    print(dict(zip(columns, record)))

print("\nSTRING ID EXAMPLES")
for row in con.execute("SELECT * FROM StringIds LIMIT 5"):
    print(row)

con.close()
