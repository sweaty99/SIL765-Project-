# Report: TLS Downgrade Attacks — Big Picture, Historical Attacks, and the Demo

This report is structured in three parts to support your contribution: (A) the big picture on modern feasibility and why forced downgrades are mostly impractical today; (B) concise explanations of historical downgrade-related attacks; (C) what this project implements, and up-to-which-year the attacks would have been feasible along with the mitigation that removed each attack vector.

Part A — Big picture: why forced downgrades are largely impractical now
-------------------------------------------------------------------

- Removal of legacy protocol support: Server and client stacks have removed SSLv2/SSLv3 and frequently TLS 1.0/1.1. If a server doesn't advertise an old version, you cannot downgrade to it.
- TLS_FALLBACK_SCSV: Clients include this value when retrying with lower versions; servers that still support higher versions can detect and abort unexpected fallbacks.
- Default strong configurations: Modern browser and server distributions disable weak ciphers (export ciphers, RC4, 3DES in many configurations), use AEAD ciphers, and prefer forward-secure key exchange (ECDHE).
- TLS 1.3 changes: TLS 1.3 removed many legacy negotiation options and authenticates more handshake data, shrinking downgrade surface.
- Operational best practices: HSTS, Certificate Transparency, OCSP stapling and CA ecosystem changes (deprecating SHA-1) make large-scale silent downgrade exploitation harder to hide.

Conclusion (short): An attacker aiming to force a downgrade today faces hard blockers: the server may simply not offer legacy versions, clients signal fallbacks via SCSV, and TLS 1.3 plus modern ciphers/PKI practices close many practical attack paths.

Part B — How key historical downgrade-related attacks worked (concise summaries)
--------------------------------------------------------------------------

- POODLE (2014)
  - Mechanism: Attacker coerces a fallback to SSLv3 (often by interfering with initial handshakes). SSLv3's block-cipher padding can then be abused as an oracle to decrypt content byte-by-byte.
  - Root cause: Legacy protocol (SSLv3) with bad padding handling and silent fallback behavior.

- FREAK (2015)
  - Mechanism: Attacker forces use of export-grade RSA keys; those weak keys could be factored, enabling decryption of sessions.
  - Root cause: Historical export-grade crypto left enabled on some servers/clients.

- Logjam (2015)
  - Mechanism: Downgrade to weak Diffie-Hellman parameters (export-grade) or exploit servers using small DH groups; then attack the DH exchange.
  - Root cause: Use of small, shared DH groups and acceptance of downgraded parameters.

- DROWN (2016)
  - Mechanism: Cross-protocol attack that exploited servers supporting SSLv2 with the same RSA key used for TLS; SSLv2 weaknesses allowed recovery of TLS secrets.
  - Root cause: Shared private keys across insecure legacy protocols and SSLv2's severe weaknesses.

Part C — What this demo implements and 'up-to-which-year' it would work
---------------------------------------------------------------------

What the demo contains
- A "modern" TLS server (`server_modern.py`) that requires TLS 1.2+ and logs negotiated versions/ciphers.
- A "legacy" TLS server (`server_legacy.py`) intentionally configured to allow TLS 1.0 (educational; not recommended for production).
- A modern client (`client_modern.py`) that requires TLS 1.2+.
- A fallback-simulating client (`client_with_fallback.py`) that demonstrates how a vulnerable client might retry with lower versions if the first handshake appears to fail.
- A plaintext simulated client/server (`simulated_client.py`, `simulated_server.py`) and a visual web UI (`demo/web`) which allow interactive exploration of negotiation, attacker stripping simulation, and timeline animations.

Up-to-which-year would these attacks have worked?
- Before 2014 (POODLE era): Forcing fallback to SSLv3 and exploiting padding or protocol weaknesses was practical against many servers and browsers. POODLE pushed rapid deprecation of SSLv3.
- 2014–2015: TLS_FALLBACK_SCSV was introduced in 2014 and started being deployed; browsers and servers moved to disable SSLv3 and export ciphers. Attacks like FREAK and Logjam (2015) exploited remaining weak configurations.
- By 2016–2017: DROWN (2016) and the SHA-1 collision proofs (2017) accelerated removal of SSLv2/legacy keys and SHA-1 certs. The practical window for many of these downgrades was closing rapidly during 2014–2017.

Mapping individual demo behaviors to historical fixes
- Client fallback behavior (what `client_with_fallback.py` simulates):
  - Would have been exploitable before TLS_FALLBACK_SCSV deployment (~2014). After SCSV and client/server updates, servers can detect malicious fallbacks and abort.

- Negotiating legacy TLS 1.0 (what `server_legacy.py` represents):
  - Servers that still accepted TLS 1.0/SSLv3 in 2014–2016 were susceptible to downgrade-based techniques and padding/legacy-cipher issues; modern deployments removed these by 2016–2018.

- Export-grade cipher stripping (attacker simulation in UI):
  - This class of weakness was common before 2015 (FREAK); after patches and config changes in 2015, export ciphers were largely disabled.

- Cross-protocol issues (DROWN):
  - DROWN specifically required SSLv2 enabled with shared RSA keys (2016 disclosure prompted immediate remediation in most places).

Final remarks
- The demo is intentionally conservative and educational. It reproduces the negotiation surface and shows how fallback behavior could lead to weaker agreements; it does not perform MITM manipulation of real TLS traffic.
- Historically, the high-risk period for these downgrade methods spans roughly 2010–2016 depending on the specific vulnerability; after that, widespread mitigation and protocol evolution (TLS 1.3) greatly reduced the attack surface.

References and further reading
- RFC 5246 (TLS 1.2) and RFC 8446 (TLS 1.3)
- Original advisories and writeups: POODLE (Google Security Blog), FREAK advisory, Logjam writeup, DROWN advisory
- OpenSSL, Mozilla, and Cloudflare blogs on deprecating SHA-1 and moving to TLS 1.3
