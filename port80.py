import urllib.request

host = "164.92.126.208"
port = 80

# Explore port 80 - Flag Hunter portal
print("=== Port 80 - Flag Hunter 2.1 ===")

url = f"http://{host}:{port}/"
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req, timeout=10)
body = resp.read().decode("utf-8", errors="replace")
print(f"Status: {resp.status}")
print(f"Length: {len(body)}")

# Print first 3000 chars
clean = body[:3000].encode("ascii", errors="replace").decode("ascii")
print(clean)
print(f"... (total {len(body)} bytes)")

# Check for cookie/session info
for k, v in resp.headers.items():
    if "cookie" in k.lower() or "session" in k.lower():
        print(f"  {k}: {v}")
