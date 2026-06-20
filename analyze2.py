import http.client, socket

host = "164.92.126.208"
ports = [80, 5001, 5002, 5003, 3000, 8000]

for port in ports:
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        print(f"\n=== Port {port} ===")
        print(f"Status: {resp.status}")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")
        # Print first 200 chars of body
        clean = body[:500].encode("ascii", errors="replace").decode("ascii")
        print(f"  Body (first 500): {clean}")
        conn.close()
    except Exception as ex:
        print(f"\n=== Port {port} === Error: {ex}")
