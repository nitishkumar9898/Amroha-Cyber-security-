import http.client, json

host = "164.92.126.208"

# Try registering on port 5003 with different approaches
# The form action is /register with POST
# Let's try to login with a preset user or register

# First, let's look at the login page more carefully to understand the form
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("GET", "/login")
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print("Login page:")
clean = body.encode("ascii", errors="replace").decode("ascii")
# Extract the form
import re
forms = re.findall(r"<form[^>]*>.*?</form>", body, re.DOTALL | re.IGNORECASE)
for f in forms:
    # Clean up
    f_clean = f.encode("ascii", errors="replace").decode("ascii")
    print(f_clean[:500])
    print("---")
conn.close()

# Try POST to login with JSON
print("\n\n=== POST /login (JSON) ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("POST", "/login", 
             json.dumps({"username": "test", "password": "test"}),
             {"Content-Type": "application/json"})
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print(f"Status: {resp.status}")
for k, v in resp.headers.items():
    print(f"  {k}: {v}")
print(f"Body: {body[:300]}")
conn.close()

# Try POST to register with JSON
print("\n\n=== POST /register (JSON) ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("POST", "/register",
             json.dumps({"username": "testuser", "password": "testpass"}),
             {"Content-Type": "application/json"})
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print(f"Status: {resp.status}")
for k, v in resp.headers.items():
    print(f"  {k}: {v}")
print(f"Body: {body[:300]}")
conn.close()
