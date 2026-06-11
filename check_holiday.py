from core import db_client
res = db_client.fetch_all("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%holiday%'")
print([dict(r) for r in res] if res else "No tables found")
