import streamlit_authenticator as stauth
from pathlib import Path
import pickle
import yaml
from yaml import SafeLoader
passwords = ["adminpass", "userpass"]

ROOT_DIR = Path(__file__).resolve().parents[1]
with open(ROOT_DIR / 'credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)


def authenticate_user(widget_name: str = "Login", location: str = "main"):
    """
    Call the Streamlit Authenticator login widget and return
    (name, authentication_status, username) when submitted,
    otherwise return (None, None, None).
    """
    result = authenticator.login(widget_name, location)
    if result:
        name, authentication_status, username = result
        return name, authentication_status, username
    return None, None, None


def render_simple_login(widget_name: str = "Login", location: str = "main"):
    """Render a simple `st.form` login UI and authenticate against
    `credentials.yaml` using the same bcrypt hashed passwords.

    Returns (name, authentication_status, username) where
    authentication_status is True/False or None when not submitted.
    """
    import streamlit as st
    from streamlit_authenticator.utilities.hasher import Hasher

    # If already authenticated in this session, return stored info
    auth = st.session_state.get("auth")
    if auth and auth.get("status"):
        return auth.get("name"), True, auth.get("username")

    container = st.sidebar if location == "sidebar" else st

    # Use non-form inputs + button to avoid duplicate-form issues when rendered from
    # multiple places. Use stable keys per widget/location to avoid Streamlit key collisions.
    base_key = f"login_{widget_name}_{location}".replace(" ", "_")
    username_key = f"{base_key}_username"
    password_key = f"{base_key}_password"
    submit_key = f"{base_key}_submit"

    container.header("🔐 Login")
    username_input = container.text_input("Username or email", key=username_key)
    password_input = container.text_input("Password", type="password", key=password_key)
    submitted = container.button("Login", key=submit_key)

    if submitted:
        users = config.get("credentials", {}).get("usernames", {})
        matched_key = None
        matched_user = None
        for key, user in users.items():
            if username_input == key:
                matched_key = key
                matched_user = user
                break
            if username_input and username_input.lower() == user.get("email", "").lower():
                matched_key = key
                matched_user = user
                break
            if username_input and username_input.lower() == user.get("name", "").lower():
                matched_key = key
                matched_user = user
                break

        if not matched_user:
            container.error("User not found. Check username or email.")
            return None, False, None

        hashed_pw = matched_user.get("password", "")
        if not hashed_pw:
            container.error("No password configured for this user.")
            return None, False, None

        if Hasher.check_pw(password_input, hashed_pw):
            name = matched_user.get("name", matched_key)
            st.session_state["auth"] = {"name": name, "status": True, "username": matched_key}
            container.success(f"Welcome {name}!")
            # Return successful authentication to caller instead of forcing a rerun
            return name, True, matched_key
        else:
            container.error("Incorrect password.")
            return None, False, None

    # Not submitted yet
    return None, None, None


def logout():
    import streamlit as st
    if "auth" in st.session_state:
        del st.session_state["auth"]


def show_simple_login_page():
    """Standalone Streamlit page for the simple login form.

    Use: streamlit run modules/login.py
    """
    import streamlit as st

    # Page config must be set before any other Streamlit UI calls
    st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")
    st.title("🔐 Simple Login (Standalone)")

    st.write("Run this page with: `streamlit run modules/login.py`")

    # Controls: allow tester to reset login or force-show the login form
    col_left, col_right = st.columns([1, 1])
    with col_right:
        if st.button("Reset login (logout)"):
            logout()
            # Try to trigger a rerun if available; otherwise user can refresh manually
            try:
                st.experimental_rerun()
            except Exception:
                pass

    show_form = st.checkbox("Show login form even if already authenticated", value=False)

    # If already authenticated and not forcing the form, show status
    auth = st.session_state.get("auth")
    if auth and auth.get("status") and not show_form:
        st.success(f"Logged in as {auth.get('name')} ({auth.get('username')})")
        st.write("You can now close this page or navigate back to your app.")
        return auth.get('name'), True, auth.get('username')

    # Render the simple login form
    name, auth_status, username = render_simple_login()

    # Display similar feedback as before
    auth = st.session_state.get("auth")
    if auth and auth.get("status"):
        st.success(f"Logged in as {auth.get('name')} ({auth.get('username')})")
    elif auth_status is False:
        st.error("Login failed. Please try again.")
    else:
        st.info("Enter your username (or email) and password, then press Login.")

    return name, auth_status, username


if __name__ == "__main__":
    show_simple_login_page()

# try:
#     # Adapt to the installed Hasher API
#     # (passwords defined above to avoid scope issues)
#     hasher = stauth.Hasher()
#     if hasattr(hasher, 'hash_list'):
#         hashed_passwords = hasher.hash_list(passwords)
#     elif hasattr(hasher, 'hash_passwords'):
#         # some versions expect credentials dict, not a raw list
#         try:
#             hashed_passwords = hasher.hash_passwords(passwords)
#         except Exception:
#             # Fall back to hashing individually
#             hashed_passwords = [hasher.hash(p) for p in passwords]
#     elif hasattr(hasher, 'hash'):
#         hashed_passwords = [hasher.hash(p) for p in passwords]
#     else:
#         raise RuntimeError(
#             "Unable to generate hashed passwords with streamlit_authenticator: no suitable Hasher method found."
#         )
# except Exception as e:
#     raise RuntimeError(
#         "Unable to generate hashed passwords with streamlit_authenticator. "
#         f"Check installed package version. Underlying error: {e}"
#     )

# # Print the hashed passwords to console if needed
# print(hashed_passwords)
