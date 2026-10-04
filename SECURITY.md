# Security Policy

## Supported Versions

We release patches and security improvements for the latest active release branch.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

We take the security and privacy of our users very seriously. ContextPot processes codebases locally, meaning your data remains strictly offline on your machine.

If you believe you have discovered a security vulnerability in ContextPot, please do **NOT** open a public GitHub issue.

Instead, please report it via private disclosure:

1. Use GitHub's private vulnerability reporting feature on this repository (under the **Security** tab).
2. Or email the maintainer directly with details at: `shaikhabdulkarim747@gmail.com`

### What to Include:
- A clear description of the vulnerability.
- Proof-of-concept steps or code to reproduce the issue.
- Potential impact on users or systems.

You will receive an acknowledgment within 48 hours, followed by updates as we investigate and address the report.

---

## Secret Redaction Disclaimer

ContextPot includes an automated sensitive-value redaction mechanism (`sanitize_content`) designed to protect common API keys, passwords, and tokens from being casually exported.

Please note:
- Redaction is a heuristic safety layer, **not** an exhaustive guarantee against all possible confidential patterns or proprietary credentials.
- Always review your exported `.txt` files before distributing them or uploading them to third-party services.
