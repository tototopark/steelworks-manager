import sys
import re

with open('core/api_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to remove app.mount and favicon and place them at the end.
mount_block = """app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Empty favicon to avoid 404 (optional if you have a real favicon in static later)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)"""

if mount_block in content:
    content = content.replace(mount_block, "")
    content += "\n\n" + mount_block + "\n"
    
    with open('core/api_router.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed routing order.")
else:
    print("mount block not found exactly.")
