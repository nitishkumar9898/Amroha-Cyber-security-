import urllib.request, http.cookiejar

host = "164.92.126.208"
port = 5002

# Test various cookies when accessing the Archivist challenge
cookies_to_test = [
    {"page": "flag"},
    {"page": "home"},
    {"flag": "true"},
    {"access": "granted"},
    {"auth": "admin"},
    {"role": "admin"},
    {"secret": "true"},
    {"bypass": "true"},
    {"debug": "true"},
    {"admin": "1"},
    {"key": "flag"},
]

print("Testing cookies on Archivist challenge...")
for cookie_dict in cookies_to_test:
    cj = http.cookiejar.CookieJar()
    for k, v in cookie_dict.items():
        from http.cookiejar import Cookie
        c = Cookie(0, k, v, None, False, host, False, False, "/", True, False, None, True, None, None, None)
        cj.set_cookie(c)
    
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    url = f"http://{host}:{port}/?page=flag"
    try:
        req = urllib.request.Request(url)
        resp = opener.open(req, timeout=5)
        body = resp.read().decode("utf-8", errors="replace")
        if resp.status == 200 and "Welcome, Seeker" not in body and "Archivist" not in body:
            print(f"INTERESTING: Cookie {cookie_dict} -> 200 with content: {body[:200]}")
        elif resp.status == 200:
            pass  # home page or main page
    except urllib.error.HTTPError as e:
        pass  # Expected
    except Exception as ex:
        pass

print("No cookie bypass found.")
