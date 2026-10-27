# New login code for Nathan's private page (maquetelegendaire.fr/espace).
# Prints the code once (give it to Nathan, never commit it) and writes only its salted SHA-256
# into wrangler.toml (ESPACE_ID, ESPACE_SALT, ESPACE_HASH). Then push to main to put it online.
# Run: python3 dev/espace_code.py [identifiant]
import hashlib, re, secrets, sys
from pathlib import Path
ident = (sys.argv[1] if len(sys.argv) > 1 else "nathan").strip().lower()
A = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
code = "-".join("".join(secrets.choice(A) for _ in range(4)) for _ in range(4))
salt = secrets.token_hex(16)
h = hashlib.sha256(f"{salt}:{ident}:{code}".encode()).hexdigest()
w = Path(__file__).resolve().parent.parent / "wrangler.toml"
t = w.read_text(encoding="utf-8")
for k, v in (("ESPACE_ID", ident), ("ESPACE_SALT", salt), ("ESPACE_HASH", h)):
    t, n = re.subn(rf'^{k} = ".*"$', f'{k} = "{v}"', t, flags=re.M)
    assert n == 1, k
w.write_text(t, encoding="utf-8")
print(f"Identifiant : {ident}\nCode : {code}")
