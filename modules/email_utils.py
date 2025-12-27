"""Utilities for extracting email addresses from web pages.

This module avoids network calls at import time (no top-level requests).
Use `extract_emails_from_url(url)` or `extract_emails_from_html(html)`.
"""

from typing import List
import re
from bs4 import BeautifulSoup
import requests
class Email_Utils:

    EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE)

# Heuristics configuration
    BLACKLIST_DOMAINS = {"example.com", "example.org", "example.net", "localhost"}
    BLACKLIST_SUBSTRINGS = {"no-reply", "noreply", "no_reply", "notify", "mailer-daemon", "postmaster"}
    TELEMETRY_SUBSTRINGS = {"sentry", "wix", "wixpress", "sentry-next"}
    IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "svg", "ico", "webp", "bmp"}

    def _clean_email(self, addr: str) -> str:
        """Trim common trailing punctuation and whitespace."""
        return addr.strip(".,;:<>\"'()[]{} ")


    def is_suspicious_email(self, addr: str) -> bool:
        """Return True if the address looks like a placeholder/telemetry/file-name (not a contact email).

        These heuristics are intentionally conservative to reduce false positives; adjust rules if
        you have legitimate addresses that are being filtered.
        """
        if not addr or '@' not in addr:
            return True
        local, _, domain = addr.partition('@')
        local = local.lower().strip()
        domain = domain.lower().strip()

        # Basic domain blacklist
        if domain in self.BLACKLIST_DOMAINS:
            return True

        # Substring checks for placeholders, no-reply, telemetry, etc.
        if any(sub in local for sub in self.BLACKLIST_SUBSTRINGS) or any(sub in domain for sub in self.BLACKLIST_SUBSTRINGS):
            return True
        if any(sub in local for sub in self.TELEMETRY_SUBSTRINGS) or any(sub in domain for sub in self.TELEMETRY_SUBSTRINGS):
            return True

        # Image/file extension in domain (e.g., '3x.jpg')
        if '.' in domain:
            ext = domain.rsplit('.', 1)[-1]
            if ext in self.IMAGE_EXTS:
                return True

        # Local part that is a long hex-like token (common for telemetry/email tokens)
        if re.fullmatch(r"[0-9a-f]{16,}", local):
            return True

        # Unreasonably long local part
        if len(local) > 64:
            return True

        # Contains suspicious punctuation or whitespace
        if any(ch in local for ch in ['/', '\\', '`', ' ']):
            return True

        return False


    def extract_emails_from_html(self, html: str) -> List[str]:
        """Return a de-duplicated list of email addresses found in the given HTML/text.

        If `filter_placeholders` is True, addresses matching common placeholder/telemetry/file patterns
        will be excluded from the returned list.
        """
        filter_placeholders = True
        if not html:
            return []

        matches = self.EMAIL_REGEX.findall(html)

        soup = BeautifulSoup(html, "html.parser")
        mailto_list: List[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if isinstance(href, str) and href.lower().startswith("mailto:"):
                addr = href.split(":", 1)[1].split("?")[0]
                mailto_list.append(addr)

        # Clean and dedupe while preserving order
        cleaned: List[str] = []
        seen = set()
        for raw in (matches + mailto_list):
            e = self._clean_email(raw)
            if not e:
                continue
            if e not in seen:
                seen.add(e)
                cleaned.append(e)

        if filter_placeholders:
            final = [e for e in cleaned if not self.is_suspicious_email(e)]
        else:
            final = cleaned

        return final



# if __name__ == "__main__":
#     import sys

#     demo_url = (
#         sys.argv[1]
#         if len(sys.argv) > 1
#         else "https://conaturalintl.com/collections/skincare?srsltid=AfmBOops7Exp0z2FQl-9YzCn6cKLUT9X-TsMVrXUk9jVTpvoiKyqyS2a"
#     )
#     results = Email_Utils.extract_emails_from_url(demo_url)
#     if results:
#         print("Found emails:", results)
#     else:
#         print("No emails found.")