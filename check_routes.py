"""
Route Checker for AIMS-FR (MTB College Management System)

Hits every GET route in the app (logged in as admin) and reports which
ones return a server error, with the exception message. Run this once
after any route/template change to catch every broken url_for(), missing
template variable, etc. in a single pass instead of clicking through the
UI one page at a time.

Usage:
    python check_routes.py
"""

import re
import sys

from app import create_app, db

app = create_app('development')
app.testing = True  # lets us see real exceptions instead of a generic 500 page


def guess_id_args(rule):
    """For routes like /students/<int:id>/edit, guess id=1 so we can at
    least hit the route. Some will 404 (no such row) - that's fine and
    expected; we only care about 500s (real bugs)."""
    args = {}
    for arg in rule.arguments:
        args[arg] = 1
    return args


with app.test_client() as client:
    # Log in as admin first so role-gated routes are reachable.
    resp = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'},
                        follow_redirects=True)
    if resp.status_code != 200:
        print(f"!! Could not log in as admin (status {resp.status_code}). "
              f"Did you run reset_and_seed.py? Aborting.")
        sys.exit(1)
    print("Logged in as admin. Checking all GET routes...\n")

    results = []
    for rule in app.url_map.iter_rules():
        if 'GET' not in rule.methods:
            continue
        if rule.endpoint == 'static':
            continue

        try:
            url = rule.rule
            args = guess_id_args(rule)
            for k, v in args.items():
                url = url.replace(f'<int:{k}>', str(v)).replace(f'<{k}>', str(v))
            r = client.get(url, follow_redirects=False)
            status = r.status_code
            detail = ""
            if status == 500:
                # Our own error handler and/or Flask's debug page both put
                # the exception text in the body somewhere - grab a snippet.
                body = r.get_data(as_text=True)
                m = re.search(r'(\w*Error: .{0,160})', body)
                detail = m.group(1) if m else body[:160].replace('\n', ' ')
            results.append((rule.endpoint, url, status, detail))
        except Exception as e:
            results.append((rule.endpoint, rule.rule, 'EXC', str(e)[:160]))

    broken = [r for r in results if r[2] == 500 or r[2] == 'EXC']
    ok = [r for r in results if r[2] not in (500, 'EXC')]

    print(f"Checked {len(results)} routes: {len(ok)} OK, {len(broken)} BROKEN\n")

    if broken:
        print("=" * 70)
        print("BROKEN ROUTES (real bugs to fix):")
        print("=" * 70)
        for endpoint, url, status, detail in broken:
            print(f"\n[{status}] {endpoint}  ({url})")
            print(f"    {detail}")

    print("\n" + "=" * 70)
    print("All other routes (200/302/404/403 are all normal here):")
    print("=" * 70)
    for endpoint, url, status, _ in ok:
        print(f"[{status}] {endpoint}  ({url})")