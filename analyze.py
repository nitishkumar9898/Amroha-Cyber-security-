import http.client, urllib.request

host = "164.92.126.208"

# Explore Port 5001 - Profile page
print("=== Port 5001 - Profile ===")
conn = http.client.HTTPConnection(host, 5001, timeout=5)
conn.request("GET", "/")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
# Print full body
clean = body.encode("ascii", errors="replace").decode("ascii")
print(clean[:2000])
conn.close()

print("\n\n=== Port 5003 - CTF Challenge ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("GET", "/")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
clean = body.encode("ascii", errors="replace").decode("ascii")
print(clean[:2000])
conn.close()
