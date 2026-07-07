"""
generate_cert.py - Run ONCE to create SSL certificate for HTTPS camera access
Usage: python generate_cert.py
Requires: pip install pyopenssl
"""
try:
    from OpenSSL import crypto
    import os, socket

    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cert_file = os.path.join(BASE_DIR, 'cert.pem')
    key_file  = os.path.join(BASE_DIR, 'key.pem')

    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"✅ SSL certificates already exist:")
        print(f"   {cert_file}")
        print(f"   {key_file}")
    else:
        print("🔐 Generating self-signed SSL certificate...")
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().CN = local_ip
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 year
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)

        # Add Subject Alternative Names for both localhost and IP
        san_list = [
            f'IP:{local_ip}',
            'IP:127.0.0.1',
            'DNS:localhost',
        ]
        san_string = ', '.join(san_list).encode()
        cert.add_extensions([
            crypto.X509Extension(b'subjectAltName', False, san_string),
            crypto.X509Extension(b'basicConstraints', True, b'CA:true'),
        ])
        cert.sign(key, 'sha256')

        with open(cert_file, 'wb') as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open(key_file, 'wb') as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

        print(f"✅ Certificate created!")
        print(f"   {cert_file}")
        print(f"   {key_file}")

    print()
    print("="*55)
    print("  Now run: python run.py")
    print(f"  Camera URL: https://{local_ip}:5000")
    print("  ⚠️  Browser will warn 'Not Secure' — click")
    print("     Advanced → Proceed to continue. This is")
    print("     normal for self-signed certificates.")
    print("="*55)

except ImportError:
    print("❌ pyopenssl not installed.")
    print("   Run: pip install pyopenssl")
