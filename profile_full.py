import urllib.request

# Get full profile page from port 5001
url = "http://164.92.126.208:5001/"
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req, timeout=5)
body = resp.read().decode("utf-8", errors="replace")

# Print the full body
clean = body.encode("ascii", errors="replace").decode("ascii")
print(clean)
print("\n--- END ---")
print(f"Total length: {len(body)}")
