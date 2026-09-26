# fastapi-review

A collection of FastAPI projects I built while learning and reviewing FastAPI. The main one is **Simple Social**, a small photo and video sharing app with a FastAPI backend and a Streamlit frontend.

| Project | Folder | What it shows |
|---|---|---|
| [Simple Social](#simple-social) | `app/` | Async SQLAlchemy, JWT auth with fastapi-users, file uploads to ImageKit, Streamlit frontend |
| [Books API](#books-api) | root (`app.py`, `books.py`, `utils.py`) | In-memory CRUD, Pydantic validation, path and query parameters |
| [Todo API](#todo-api) | `TodoAPP/` | CRUD on SQLite with synchronous SQLAlchemy |

---

## Simple Social

Users sign up, log in, upload images or videos with a caption, and see everyone's posts in a feed. You can delete only your own posts.

### Stack

- **FastAPI** for the REST API
- **fastapi-users** for registration, login, and JWT bearer tokens
- **SQLAlchemy 2 (async)** with **aiosqlite**, storing data in `app/test.db`
- **ImageKit** for media storage and delivery
- **Streamlit** for the frontend

### Project layout

```
app/
├── app.py        # FastAPI app: upload, feed, and delete routes, plus the auth routers
├── db.py         # SQLAlchemy models (User, Post), engine, session dependency
├── users.py      # fastapi-users setup: user manager, JWT strategy, auth backend
├── schemas.py    # Pydantic schemas for users
├── images.py     # ImageKit client
└── frontend.py   # Streamlit UI
```

### Setup

You need **Python 3.14+** and [uv](https://docs.astral.sh/uv/). Run these from the repo root.

1. **Install dependencies**
   ```bash
   uv sync
   source .venv/bin/activate
   ```

2. **Create `app/.env`** with your settings:
   ```env
   IMAGEKIT_PRIVATE_KEY=private_xxxxxxxxxxxxxxxx
   IMAGEKIT_PUBLIC_KEY=public_xxxxxxxxxxxxxxxx
   IMAGEKIT_URL=https://ik.imagekit.io/<your_imagekit_id>
   JWT_SECRET=<a long random string>
   ```
   - Get the ImageKit keys from your ImageKit dashboard under **Developer options**. Uploads use the **private** key, which starts with `private_`.
   - Generate a JWT secret with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
   - `.env` is listed in `.gitignore`. Never commit it.

### Running

Start the API and the frontend in two terminals, both from `app/`:

```bash
cd app
uvicorn app:app --reload        # API at http://localhost:8000
```

```bash
cd app
streamlit run frontend.py       # UI at http://localhost:8501
```

The database tables are created automatically when the API starts. Interactive API docs are at http://localhost:8000/docs.

### API

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | — | Create an account (JSON: `email`, `password`) |
| `POST` | `/auth/jwt/login` | — | Log in (form fields: `username` = your email, `password`). Returns an `access_token` |
| `POST` | `/auth/jwt/logout` | Bearer | Log out |
| `GET`, `PATCH` | `/users/me` | Bearer | View or update your profile |
| `POST` | `/upload` | Bearer | Upload a file (multipart: `file`, `caption`) and create a post |
| `GET` | `/feed` | Bearer | All posts, newest first, with the author's email and an `is_owner` flag |
| `DELETE` | `/posts/{post_id}` | Bearer | Delete a post you own (`403` if it isn't yours, `404` if it doesn't exist) |

fastapi-users also provides password reset (`/auth/forgot-password`, `/auth/reset-password`), email verification (`/auth/request-verify-token`, `/auth/verify`), and user management (`/users/{id}`). See `/docs` for details.

Example with `curl`:

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/jwt/login \
  -d "username=me@example.com&password=secret" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" \
  -F "file=@photo.jpg" -F "caption=Hello world" localhost:8000/upload

curl -H "Authorization: Bearer $TOKEN" localhost:8000/feed
```

### Notes

- **Schema changes:** `create_all` only creates tables that don't exist yet; it never changes an existing table. If you change a model in `db.py`, delete `app/test.db` (or drop the affected table) and restart. Once you have data worth keeping, use Alembic migrations instead.
- **ImageKit SDK v5:** this project uses `imagekitio` 5.x, whose API differs from the older 4.x SDK. Upload options are keyword arguments to `imagekit.files.upload(...)`; the old `UploadFileRequestOptions` class no longer exists.
- **Importing from fastapi-users:** import the SQLAlchemy classes through `fastapi_users.db`, not directly from `fastapi_users_db_sqlalchemy`. Importing the add-on first causes a circular import that silently removes `SQLAlchemyUserDatabase` from `fastapi_users.db`.

---

## Books API

An in-memory CRUD API for books; data resets on every restart. Run it from the repo root:

```bash
uvicorn app:app --reload
```

Main routes: `GET /books`, `GET /books/{book_id}`, `GET /books/search/`, `POST /create-book`, `PUT /books/{book_id}`, `DELETE /books/{book_id}`.

## Todo API

A CRUD API for todos, stored in SQLite (`TodoAPP/todos.db`) with synchronous SQLAlchemy. Run it from `TodoAPP/`:

```bash
cd TodoAPP
uvicorn main:app --reload
```

Main routes: `GET /`, `GET /todos/{todo_id}`, `POST /todos/create_todo`, `PUT /todos/{todo_id}`.

