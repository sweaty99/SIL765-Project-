# TLS Negotiation Demo (Educational)

This demo is an educational, **non-exploit** simulation of TLS negotiation and a vulnerable-style fallback behavior in an isolated environment.

It intentionally shows how a client that falls back to older TLS versions can end up negotiating weaker protocol versions if the server allows them. It does NOT perform any MITM or downgrade attacks and must only be run in a private, local environment under your control.

Files:
- `generate_certs.sh` - helper to create a self-signed certificate (`cert.pem` / `key.pem`).
- `server_modern.py` - TLS server that requires TLS 1.2+ (port 4443).
- `server_legacy.py` - TLS server that only allows TLS 1.0 (port 4444).
- `client_modern.py` - client that requires TLS 1.2+ and connects to a server.
- `client_with_fallback.py` - client that *simulates* vulnerable fallback behavior: on failure it retries with lower TLS versions (for demonstration only).
- `analyzer.py` - simple script to flag negotiations that ended up below TLS 1.2.

How to use (macOS / zsh):

1. Generate certs (runs OpenSSL locally):

```bash
cd demo
./generate_certs.sh
```

2. Start the modern server:

```bash
python3 server_modern.py
```

3. In another terminal, start the legacy server (optional, to compare):

```bash
python3 server_legacy.py
```

4. Run the modern client (connects to modern server):

```bash
python3 client_modern.py 127.0.0.1 4443
```

5. Run the client that simulates fallback behaviour (tries modern then falls back):

```bash
python3 client_with_fallback.py 127.0.0.1 4443
```

6. Use `analyzer.py` to analyze logged negotiation results.

Notes:
- This demo is for learning only. It purposefully demonstrates what happens when endpoints support and accept older protocol versions. It does not perform interception or packet manipulation.
- The scripts include comments explaining the handshake logs and where a real-world attacker might try to interfere (conceptually).

Detailed background, attacks, mitigations, diagrams, and Q&A
----------------------------------------------------------

This section collects the theory you asked for so you can read and understand the subject end-to-end.

1) TLS negotiation (short, conceptual contract)
- Inputs: ClientHello (supported versions, cipher suites, extensions), ServerHello (chosen version, cipher), certificates, key-exchange messages.
- Output: Agreed TLS version, chosen cipher suite, and shared keys used for secure application data.
- Error modes: version mismatch, unsupported cipher suites, certificate validation failures, handshake aborts.

2) Where downgrade attacks fit in (conceptual)
- A downgrade attack tries to influence which version/cipher is selected so a weaker one is agreed. Typical interference points:
	- Preventing or dropping the initial handshake so the client retries with lower versions.
	- Stripping strong cipher suites from the ClientHello so the server selects a weaker suite.
	- Exploiting implicit or explicit fallback behavior in clients that retry on failure.

3) Short attack summaries and key takeaways (historical)

- POODLE (2014)
	- What: Attacker induced fallback to SSLv3 and exploited block-cipher padding handling to recover bytes.
	- Why it mattered: SSLv3 had fundamental weaknesses; many servers/clients allowed fallbacks.
	- Takeaway: Remove SSLv3 support and do not silently fallback to old protocols.

- FREAK (2015)
	- What: Attackers forced the use of export-grade RSA keys; when servers accepted those weak keys, attackers could recover session keys.
	- Why it mattered: Legacy export-cipher support remained in some servers/clients.
	- Takeaway: Disable export ciphers, prefer forward-secure (DHE/ECDHE) exchanges.

- Logjam (2015)
	- What: Downgrade to weak Diffie-Hellman groups (export-grade) allowed discrete-log attacks on DH and breaking key exchange.
	- Why it mattered: Many servers used small or shared DH groups; some clients accepted downgraded groups.
	- Takeaway: Use strong DH params (2048+ bits) or prefer ECDHE (curve25519, secp256r1).

- DROWN (2016)
	- What: Cross-protocol attack exploiting servers that supported SSLv2 with the same RSA key to break TLS.
	- Why it mattered: Shared private keys across protocols created unexpected attack surfaces.
	- Takeaway: Remove SSLv2/SSLv3 support and avoid sharing keys across unsupported legacy protocols.

4) SHA-1 role and concerns
- SHA-1 was used for certificate signatures and legacy TLS MACs. Collision attacks make SHA-1 unsuitable for signature assurance.
- Takeaway: Use SHA-256+ signatures and prefer modern cipher suites that use AEAD and modern hashes.

5) Protocol mitigations (what protocols/implementations added)
- TLS_FALLBACK_SCSV: a signal added to ClientHello to indicate a deliberate fallback attempt; servers seeing it and also supporting higher versions can abort, preventing attacker-forced fallbacks.
- TLS 1.3: redesign that removes many legacy options and authenticates more handshake data, reducing downgrade vectors.
- Remove legacy support: servers and clients should disable SSLv2/SSLv3/TLS1.0/TLS1.1 and export ciphers.

6) Detection and forensic indicators
- Unexpected protocol versions in logs (sudden TLS 1.0/SSLv3 sessions from modern clients).
- Repeated handshake retries from same client IP; unusual TLS alerts (protocol version alerts).
- Presence of TLS_FALLBACK_SCSV in ClientHello without corresponding ServerHello support or unexpected responses.

7) Defensive checklist (server + client)
- Servers:
	- Disable SSLv2/SSLv3 and TLS1.0/1.1.
	- Disable export/weak ciphers; favor AEAD ciphers (AES-GCM, ChaCha20-Poly1305).
	- Use ECDHE/DHE with strong groups (curve25519 or 2048+ DH) for forward secrecy.
	- Prefer TLS 1.3; enable HSTS and OCSP stapling.
	- Use certificates signed with SHA-256 or stronger algorithms.

- Clients:
	- Reject SHA-1-signed certificates and warn users.
	- Do not silently fallback; implement TLS_FALLBACK_SCSV behavior.
	- Keep root stores and TLS libraries up to date.

8) Diagrams (ASCII)

Client-server happy path (modern):

	Client                      Network                      Server
	------                      -------                      ------
	ClientHello (v1.3, v1.2) -->                           ServerHello (v1.3)
						<-- ServerHelloDone (v1.3)                  Certificate, KeyExchange
	Finished -->                                           Finished
	Application Data <-->  (Encrypted with agreed keys)

Downgrade scenario (conceptual):

	Client                      Attacker                      Server
	------                      --------                      ------
	ClientHello (v1.3, v1.2) -->  DROP/ALTER   -->            Server receives only older options
																														ServerHello (v1.0)
	Client retries (fallback) -->                            ServerHello (v1.0)
	Application Data <-->  (Weaker crypto negotiated)

9) Q&A and exam-style sample questions
- Q: What is TLS_FALLBACK_SCSV and why is it important?
	A: A signaling value sent by clients when they intentionally retry a connection at a lower version; servers that support higher versions can detect unwanted fallbacks and abort.

- Q: Name two historical attacks that exploited downgrade/fallback behavior.
	A: POODLE and FREAK (also Logjam and DROWN are related historical incidents).

- Q: How does TLS 1.3 reduce the risk of downgrade attacks?
	A: It removes legacy algorithm choices, authenticates more handshake data, and simplifies handshakes to avoid downgradeable states.

10) Further reading (recommended)
- RFC 5246 (TLS 1.2)
- RFC 8446 (TLS 1.3)
- Google Project Zero / vendor writeups on POODLE, FREAK, Logjam, DROWN
- OpenSSL and Mozilla security blog posts on deprecating SHA-1 and old TLS versions

11) Where this repo fits
- The code here demonstrates negotiation behavior and shows, in a controlled setting, how a client fallback can end in negotiation of older versions if servers allow them. It does not and should not provide methods to force downgrades in third-party systems.

Web visualization
-----------------
There is a small static web UI in `web/` that visualizes a handshake flow and lets you pick server mode (modern vs legacy). It uses no external libs and runs locally.

Security & ethics
-----------------
Only run these demos in an isolated environment you control. Do not attempt to use these techniques against systems you do not own or have explicit permission to test.

Demo vs real life — what's different, and could this attack be implemented now?
---------------------------------------------------------------------

This project is an educational simulation; the environment here deliberately simplifies and isolates TLS negotiation so you can observe behaviors without performing any real-world attack. Below are the differences between this demo and a real on-the-wire downgrade attack, why many such attacks are no longer practical, and a short historical timeline showing when specific defenses became widely deployed.

Key differences between this demo and a real-world downgrade attack
- Control: In the demo you control both endpoints or run a simulated plaintext server. In the real world an attacker does not control the server and must interfere remotely in the network path.
- Visibility: The demo logs and shows negotiation data in clear text for learning. Real TLS handshakes are encrypted after the handshake and packet-level manipulation requires intercepting or dropping packets on the network.
- Consent and scope: The demo is run in a lab you own. Real attacks require authorization and often cross legal boundaries.
- Capability assumptions: The plaintext simulator can force server behavior (legacy vs modern) because you run the server. Real servers vary and many have removed legacy support.

Why similar attacks are often not implementable today (short answers)
- Many servers and clients have removed support for SSLv2/SSLv3 and TLS 1.0/1.1. You cannot downgrade to protocol versions the server refuses to speak.
- TLS_FALLBACK_SCSV prevents many forced-fallback techniques by allowing servers to detect unexpected fallbacks and abort the handshake.
- Browsers and major libraries refuse to accept certificates signed with SHA-1 and disable weak cipher suites by default — this reduces the utility of downgrading.
- TLS 1.3 removed many legacy negotiation choices and authenticates more of the handshake, removing earlier downgrade windows.
- Operational practices (HSTS, CT, pinning in some deployments) and alerting make it easier to detect suspicious downgrade or retry behavior.

When were these protections deployed? A brief timeline
- 2014: POODLE disclosure; SSLv3 was rapidly deprecated by browsers and vendors.
- 2014: TLS_FALLBACK_SCSV was standardized and deployed to prevent forced fallback attacks.
- 2015: FREAK and Logjam disclosed — vendors began disabling export ciphers and recommending strong DH/ECDHE parameters.
- 2016: DROWN disclosed — servers were audited and SSLv2 support was removed.
- 2017: Practical SHA-1 collision published; browsers and CAs deprecated SHA-1-signed certificates around this time.
- 2018–2020: TLS 1.3 adoption accelerated; clients and servers defaulted to stronger cipher suites and AEAD constructions.

Are there exceptions — when could a real-world downgrade still work?
- Legacy, misconfigured, or embedded devices: Systems still allowing very old TLS or export ciphers remain vulnerable, particularly in industrial control, embedded, or outdated enterprise stacks.
- Split private networks: If an attacker controls routing inside a LAN or if endpoints share a misconfigured middlebox that downgrades or proxies TLS, a downgrade could be forced in that controlled network.
- Outdated client software: If a client is older and still willing to fall back, and a server advertises or accepts a weak option, a downgrade path exists.

Practical takeaways
- For research and education, use the provided demo and simulated server to understand the negotiation flow and how downgrade conditions can appear.
- For defensive work, prioritize removing legacy protocol/cipher support, enabling TLS 1.3, and ensuring client libraries treat fallbacks with TLS_FALLBACK_SCSV semantics.
- Always test in isolated environments and obtain permission before probing or testing real services.


