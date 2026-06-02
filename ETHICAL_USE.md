# Ethical & Authorized Use

airt is for **defensive AI security testing of systems you own or are explicitly
authorized to test.**

- Run only against targets with `authorized: true` AND a signed authorization on file.
- Never test third-party or out-of-scope systems.
- No credential theft, malware, or live exploitation beyond demonstrating the AI flaw.
- Evidence is redacted by default; raw retention requires explicit opt-in and ROE permission.
- See the master blueprint, Section 17, for the full policy and authorization-form fields.

The `target.authorized` flag is enforced in code: `airt run` exits with code 3 if a
target is not marked authorized.
