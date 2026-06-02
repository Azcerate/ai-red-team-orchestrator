# Security Policy

## Scope & intent
airt is a **defensive** tool for testing AI systems you own or are authorized to
test. The `target.authorized` flag is enforced: `airt run` exits with code 3 for
unauthorized targets. Do not use airt against third-party systems without written
permission.

## Reporting a vulnerability
Please report security issues privately to **asaunders@dmcslabs.com** rather than
opening a public issue. Include reproduction steps and impact. We aim to acknowledge
within 5 business days.

## Handling sensitive data
Evidence is redacted by default. Do not commit real canary tokens, client data, or
raw responses containing secrets. Raw retention is opt-in and should follow your
rules of engagement.
