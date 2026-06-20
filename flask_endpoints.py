import urllib.request

host = "164.92.126.208"
port = 5002

# Try to discover hidden Flask endpoints on port 5002
url_paths = [
    # Common Flask endpoints
    "/admin", "/admin/", "/api", "/api/", "/v1", "/v1/",
    "/health", "/healthcheck", "/status", "/ping",
    "/_debug", "/_debug/", "/debug", "/debug/",
    "/config", "/config/",
    "/env", "/env/",
    "/shell", "/shell/",
    "/exec", "/exec/",
    "/flag", "/flag/",
    "/page", "/page/",
    "/pages", "/pages/",
    "/scroll", "/scrolls",
    "/doc", "/docs",
    "/source", "/source/",
    "/src", "/src/",
    "/.env", "/.git", "/.git/",
    "/robots.txt", "/sitemap.xml",
    "/Dockerfile", "/docker-compose.yml",
    # Try with .php extension
    "/index.php", "/home.php", "/flag.php",
    "/admin.php", "/config.php",
    # Subpaths
    "/app", "/app/",
    "/app.py", "/main.py", "/server.py",
    "/requirements.txt",
    # Try to traverse
    "/../flag", "/..%2fflag",
    "/static/", "/static/../flag",
    "/templates/", "/templates/../flag",
    # Different methods
]

for path in url_paths:
    url = f"http://{host}:{port}{path}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read().decode("utf-8", errors="replace")
        if resp.status == 200:
            clean = body.encode("ascii", errors="replace").decode("ascii")
            print(f"200: {path} -> {clean[:200]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if "Access Denied" in body:
            pass  # App's 404
        elif e.code != 404:
            print(f"{e.code}: {path}")
    except Exception as ex:
        print(f"ERR: {path} -> {ex}")

print("Done exploring endpoints.")
