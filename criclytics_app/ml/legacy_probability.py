"""Retired compatibility entry point; no I/O, network or deserialization."""


def main():
    raise SystemExit('This legacy command is retired. See docs/AUDIT_REMEDIATION.md for supported workflows.')


if __name__ == "__main__":
    main()
