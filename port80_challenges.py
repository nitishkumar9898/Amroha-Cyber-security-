import urllib.request

host = "164.92.126.208"

# Get the challenges page from port 80
url = f"http://{host}:80/challenges"
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req, timeout=10)
body = resp.read().decode("utf-8", errors="replace")
clean = body.encode("ascii", errors="replace").decode("ascii")
print(clean[:5000])

# Also get the main page for API endpoints
url = f"http://{host}:80/api/v1/challenges"
req = urllib.request.Request(url)
try:
    resp = urllib.request.urlopen(req, timeout=5)
    body = resp.read().decode("utf-8", errors="replace")
    print("\n\n=== API /api/v1/challenges ===")
    print(body[:2000])
except Exception as ex:
    print(f"API error: {ex}")
