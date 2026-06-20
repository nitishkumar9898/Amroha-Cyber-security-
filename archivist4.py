import urllib.request

host = "164.92.126.208"
port = 5002

# Test Python 'or' operator falsy bypass
tests = ['0', 'false', 'False', 'None', 'null', '', ' ', 'home', 'home.php', '0.0', '0x0', '[]', '()', '{}', 'nil', 'off', 'no']

for v in tests:
    url = f"http://{host}:{port}/?page={v}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read().decode("utf-8", errors="replace")
        if resp.status == 200:
            clean = body.encode("ascii", errors="replace").decode("ascii")
            print(f'200: "{v}" -> {clean[:100]}')
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass

print("Done")
