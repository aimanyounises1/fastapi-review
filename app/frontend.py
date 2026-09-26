import streamlit as st
import requests
import urllib.parse

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Simple Social", layout="wide")

if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

def error_detail(response):
    try:
        return response.json().get("detail", response.text)
    except ValueError:
        return response.text

def resized_url(url, width=800):
    """Ask ImageKit for a resized copy; leave other hosts' URLs untouched."""
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "ik.imagekit.io":
        return url
    endpoint, _, path = parsed.path.lstrip("/").partition("/")
    return f"{parsed.scheme}://{parsed.netloc}/{endpoint}/tr:w-{width}/{path}"

def login_page():
    st.title("Welcome Simple Social")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    login_button = col1.button("Login", width="stretch")
    signup_button = col2.button("Sign up", width="stretch")

    if login_button:
        if not email or not password:
            st.error("Please enter your email and password.")
            return
        response = requests.post(f"{API_URL}/auth/jwt/login",
                                 data={"username": email, "password": password})
        if response.status_code != 200:
            st.error(f"Login failed: {error_detail(response)}")
            return
        st.session_state.token = response.json()["access_token"]
        me = requests.get(f"{API_URL}/users/me", headers=get_headers())
        st.session_state.user = me.json() if me.ok else {"email": email}
        st.rerun()

    if signup_button:
        if not email or not password:
            st.error("Please enter an email and password to sign up.")
            return
        response = requests.post(f"{API_URL}/auth/register",
                                 json={"email": email, "password": password})
        if response.status_code == 201:
            st.success("Account created. You can log in now.")
        else:
            st.error(f"Sign up failed: {error_detail(response)}")

def feed_page():
    st.title("Feed")

    response = requests.get(f"{API_URL}/feed", headers=get_headers())
    if response.status_code == 401:
        st.warning("Your session expired. Please log in again.")
        logout()
    if not response.ok:
        st.error(f"Could not load the feed: {error_detail(response)}")
        return

    posts = response.json()
    if not posts:
        st.info("No posts yet. Be the first to upload one!")
        return

    for post in posts:
        with st.container(border=True):
            st.caption(f"{post['email']} · {post['created_at'][:16].replace('T', ' ')}")
            if post["file_type"] == "video":
                st.video(post["url"])
            else:
                st.image(resized_url(post["url"]), width="stretch")
            if post["caption"]:
                st.write(post["caption"])
            if post["is_owner"] and st.button("Delete", key=f"delete_{post['id']}"):
                delete = requests.delete(f"{API_URL}/posts/{post['id']}", headers=get_headers())
                if delete.ok:
                    st.success("Post deleted.")
                    st.rerun()
                else:
                    st.error(f"Delete failed: {error_detail(delete)}")

def upload_page():
    st.title("New post")

    uploaded_file = st.file_uploader("Choose an image or video",
                                     type=["png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "webm"])
    caption = st.text_area("Caption")

    if st.button("Share", disabled=uploaded_file is None):
        with st.spinner("Uploading..."):
            response = requests.post(
                f"{API_URL}/upload",
                headers=get_headers(),
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                data={"caption": caption},
            )
        if response.ok:
            st.success("Posted!")
        elif response.status_code == 401:
            st.warning("Your session expired. Please log in again.")
            logout()
        else:
            st.error(f"Upload failed: {error_detail(response)}")

def main():
    if not st.session_state.token:
        login_page()
        return

    with st.sidebar:
        st.write(f"Logged in as **{st.session_state.user.get('email', '')}**")
        page = st.radio("Go to", ["Feed", "New post"])
        if st.button("Log out"):
            logout()

    if page == "Feed":
        feed_page()
    else:
        upload_page()

main()
