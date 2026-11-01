# Security policy

## Reporting

Use GitHub Security Advisories. Do not paste API keys, MongoDB URIs, or private book paths into an issue.

## Secrets

Keys are read from the environment. The tree ships empty placeholders in `.env.example` only. There is no embedded key, connection string, or cloud credential.

## Demo

`python3 demo.py` writes one local Markdown file. It does not open a network connection.

## Data

Do not commit `data/`, `.env`, or downloaded books. `.gitignore` already excludes them.
