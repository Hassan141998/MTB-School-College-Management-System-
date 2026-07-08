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


def guess_id_args(rule):
    """For routes like /students/<int:id>/edit, guess id=1 so we can at
    least hit the route. Some will 404 (no such row) - that's fine and
    expected; we only care about 500s (real bugs)."""
    args = {}
    for arg in rule.arguments:
        args[arg] = 1
    return args


def main():
    from app import create_app

    app = create_app('development')
    app.testing = True  # lets us see real exceptions instead of a generic 500 page
    # IMPORTANT: without this, Flask-WTF's CSRF protection silently rejects
    # the automated login below (no real browser/token), every subsequent
    # request bounces to /auth/login, and every route falsely reports 302.
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        # Log in as admin first so role-gated routes are reachable.
        resp = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'},
                            follow_redirects=True)
        final_url = resp.request.path if hasattr(resp, 'request') else ''
        if resp.status_code != 200 or 'login' in (resp.request.path or ''):
            print(f"!! Login did not succeed (ended on {resp.request.path}, "
                  f"status {resp.status_code}). Did you run reset_and_seed.py "
                  f"and is admin/admin123 valid? Aborting.")
            sys.exit(1)
        print("Logged in as admin. Checking all GET routes...\n")

        results = []
        for rule in app.url_map.iter_rules():
            if 'GET' not in rule.methods:
                continue
            if rule.endpoint == 'static':
                continue
            if rule.endpoint in ('auth.logout', 'auth.login'):
                # logout actually ends the session mid-sweep (was silently
                # causing every route checked afterward to false-report
                # 302 for the rest of the run); login redirects away when
                # already authenticated, which is correct, not a bug.
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
        print("All other routes (expect 200 now that CSRF/login is fixed; "
              "302 here would mean a genuine access-control issue):")
        print("=" * 70)
        for endpoint, url, status, _ in ok:
            print(f"[{status}] {endpoint}  ({url})")


if __name__ == "__main__":
    # Guard is essential: this must ONLY run via `python check_routes.py`.
    # Do NOT set FLASK_APP=check_routes.py or run it with `flask run` -
    # that imports this file as a side effect and also tries to serve it
    # as a web app, which is not what this script is for.
    main()