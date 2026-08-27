# USAGE

Once the application is running, open your browser to `http://127.0.0.1:5000`.

## Web Interface

### Public Home Page

Visiting `/` without logging in shows the six top-rated books on the platform.

### Registration

Navigate to `/register`. Provide a username (≥2 characters), email, and password (≥6 characters). After successful registration you are redirected to the login page.

### Login / Logout

Go to `/login` and enter your email and password. Once authenticated you can access all member features. Click **Logout** (or visit `/logout`) to end your session.

### Books

- **Browse books** at `/books`. The page supports:
  - Full‑text search by title, author, or description (`?q=` query parameter).
  - Filtering by genre (`?genre=`).
  - Sorting by title, publication year, or average rating (`?sort=title|year|rating`).
  - Pagination (`?page=`).

- **Add a book** at `/books/add` (requires login). Fill in title, author, genre, publication year, cover image URL, and description.

- **View a book** at `/books/<id>`. The page shows:
  - Book details.
  - Average rating (if any).
  - The currently logged‑in user’s shelf status (Want to Read, Reading, Read) and a dropdown to change it.
  - All reviews, each with an option for the author (or an admin) to edit or delete.

- **Edit a book** at `/books/<id>/edit` (admins only).
- **Delete a book** via POST to `/books/<id>/delete` (admins only).

### Reviews

- **Write a review** from the book detail page. Each user can write only one review per book. Choose a rating (1–5) and add optional text.
- **Edit a review** at `/reviews/<review_id>/edit` (author or admin).
- **Delete a review** via POST to `/reviews/<review_id>/delete` (author or admin).

### Shelves

On any book’s detail page, use the dropdown to place the book on your **Want to Read**, **Reading**, or **Read** shelf. The current shelf is highlighted.

### Profile & Social

- Visit `/users/<user_id>` to see a user’s public profile:
  - Books shelved in each category.
  - Recent reviews.
  - Follower / following counts.
- **Follow / unfollow** a user via a POST to `/follow/<user_id>` (toggle).

### Activity Feed

Logged‑in users see a personalized activity feed on the home page, showing recent reviews and shelf updates from followed users.

## JSON API

The API prefix is `/api`.

### `GET /api/books`

Returns a paginated list of books with average ratings.

**Query parameters:**

- `page` – page number (default 1)
- `genre` – filter by genre
- `sort` – `title` (default), `year`, or `rating`
- `q` – search term (matches title, author, description)

**Example:**

```bash
curl "http://127.0.0.1:5000/api/books?genre=Fantasy&sort=rating&page=2"
```

**Response:**

```json
{
  "books": [
    {
      "id": 3,
      "title": "The Name of the Wind",
      "author": "Patrick Rothfuss",
      "cover_url": "...",
      "genre": "Fantasy",
      "publication_year": 2007,
      "description": "...",
      "average_rating": 4.65
    }
  ],
  "page": 2,
  "per_page": 12,
  "total": 45,
  "pages": 4
}
```

### `GET /api/books/<id>`

Returns a single book with its average rating and review count.

**Example:**

```bash
curl "http://127.0.0.1:5000/api/books/1"
```

**Response:**

```json
{
  "id": 1,
  "title": "Dune",
  "author": "Frank Herbert",
  "cover_url": "...",
  "genre": "Science Fiction",
  "publication_year": 1965,
  "description": "...",
  "average_rating": 4.8,
  "review_count": 12
}
```

If the book does not exist, a `404` is returned with an error object.

## Demo Data

If the environment variable `BOOKHIVE_ALLOW_SEED=1` is set, the application seeds a few demo books and an admin user on first launch. The admin email is `admin@bookhive.local` with password `adminpass` (change immediately in production).