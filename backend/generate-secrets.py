#!/usr/bin/env python3
"""Run locally or in cPanel Terminal; copy outputs to cPanel environment variables."""
import secrets
print('FPP_STREAM_TOKEN='+secrets.token_urlsafe(48))
print('FPP_PAIR_CODE='+secrets.token_urlsafe(20))
