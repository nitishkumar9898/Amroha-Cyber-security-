import http.client, json

host = "164.92.126.208"

# Explore port 5003 more - it has registration and login forms
# First check the /register page
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("GET", "/register")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print("=== /register ===")
clean = body[:1500].encode("ascii", errors="replace").decode("ascii")
print(clean)
conn.close()

# Try login
print("\n\n=== /login (GET) ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("GET", "/login")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
clean = body[:1500].encode("ascii", errors="replace").decode("ascii")
print(clean)
conn.close()

# Try to POST register with proper content type
print("\n\n=== POST /register ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("POST", "/register", 
             "username=admin&password=admin123", 
             {"Content-Type": "application/x-www-form-urlencoded"})
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print(f"Status: {resp.status}")
for k, v in resp.headers.items():
    print(f"  {k}: {v}")
print(f"Body: {body[:500]}")
conn.close()
