import streamlit_authenticator as stauth
from pathlib import Path
import pickle
passwords = ["adminpass", "userpass"]

try:
    # Adapt to the installed Hasher API
    # (passwords defined above to avoid scope issues)
    hasher = stauth.Hasher()
    if hasattr(hasher, 'hash_list'):
        hashed_passwords = hasher.hash_list(passwords)
    elif hasattr(hasher, 'hash_passwords'):
        # some versions expect credentials dict, not a raw list
        try:
            hashed_passwords = hasher.hash_passwords(passwords)
        except Exception:
            # Fall back to hashing individually
            hashed_passwords = [hasher.hash(p) for p in passwords]
    elif hasattr(hasher, 'hash'):
        hashed_passwords = [hasher.hash(p) for p in passwords]
    else:
        raise RuntimeError(
            "Unable to generate hashed passwords with streamlit_authenticator: no suitable Hasher method found."
        )
except Exception as e:
    raise RuntimeError(
        "Unable to generate hashed passwords with streamlit_authenticator. "
        f"Check installed package version. Underlying error: {e}"
    )

# Print the hashed passwords to console if needed
print(hashed_passwords)
