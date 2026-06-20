import http.client

host = "164.92.126.208"

# Explore port 5003 - CTF Challenge / Account Portal
print("=== Port 5003 - Full exploration ===")

# GET / - main page
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("GET", "/")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print("GET /:")
print(body[:1000])
conn.close()

# Try login page
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("GET", "/login")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print("\n\nGET /login:")
print(body[:500])
conn.close()

# Try register via POST to create a user
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("POST", "/register", "username=testuser&password=testpass", 
             {"Content-Type": "application/x-www-form-urlencoded"})
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print("\n\nPOST /register:")
print(body[:500])
# Check for redirect or session cookie
for k, v in resp.headers.items():
    print(f"  Header: {k}: {v}")
conn.close()
