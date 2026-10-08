# Student Records Manager

A student directory and CRUD API built with FastAPI, SQLAlchemy, and SQLite. The dashboard supports record management and filtering. An optional local Ollama model can answer natural-language questions about student data.

## Features

- Create, view, update, and delete student records.
- Search and filter students by name, course, and date of birth.
- View enrollment summaries and course distribution in the dashboard.
- Validate required fields, contact details, dates, and duplicate email addresses.
- Store records locally in `students.db`.
- Ask questions about student records with Ollama.

## Requirements

- Python 3.10 or newer.
- pip, included with standard Python installations.
- Ollama is optional and is only required for the AI assistant.

## 1. Set Up the Environment

Open a terminal in the project root, the directory containing `requirements.txt`.

Create a virtual environment:

```bash
# macOS and Linux
python3 -m venv .venv

# Windows
py -m venv .venv
```

Activate it:

```bash
# macOS and Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

When the environment is active, install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Start the Application

From the project root, run:

```bash
python -m uvicorn app.main:app --reload
```

Keep this terminal open while using the application. Uvicorn reloads the server when Python files change.

Open these pages in a browser:

- Dashboard: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs
- Alternative API documentation: http://127.0.0.1:8000/redoc

The application creates `students.db` and its tables automatically on startup. Existing records remain in that database between runs.

## 3. Add Optional Sample Records

To populate an empty database with five fictional students, run this command from the project root:

```bash
python seed_data.py
```

The script adds records only when the database is empty. It does not replace or append to an existing populated database. This step is optional; records can also be added through the dashboard or API.

## 4. Manage Student Records

The dashboard provides forms for creating and editing records, a searchable directory, course filters, and delete actions. The main API endpoints are:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/students` | Create a student |
| `GET` | `/students` | List students; supports filters and pagination |
| `GET` | `/students/{student_id}` | Get one student |
| `PUT` or `PATCH` | `/students/{student_id}` | Update a student |
| `DELETE` | `/students/{student_id}` | Delete a student |
| `POST` | `/ask` | Ask the optional AI assistant a question |

For example, create a record with curl:

```bash
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Meera Nair","date_of_birth":"2005-08-14","email":"meera@example.com","course":"AI & ML"}'
```

Filter records using query parameters:

```bash
curl "http://127.0.0.1:8000/students?name=meera"
curl "http://127.0.0.1:8000/students?course=AI&born_after=2005-01-01"
```

The list endpoint also supports `born_before`, `skip`, and `limit`. Dates use the `YYYY-MM-DD` format. The default page size is 100 records; the maximum is 500.

### Student Fields and Validation

| Field | Requirement | Notes |
|---|---|---|
| `name` | Required | 2-100 characters |
| `date_of_birth` | Required | Must be earlier than today |
| `email` | Email or phone required | Must be a valid email address; unique when supplied |
| `phone` | Email or phone required | 7-15 characters from digits, spaces, and hyphens, with an optional leading `+` |
| `course` | Optional | Up to 100 characters |
| `address` | Optional | Up to 255 characters |
| `enrollment_date` | Optional | Use `YYYY-MM-DD` |

The API returns `404` when a student does not exist, `409` for a duplicate email, and `422` when request data fails validation.

## 5. Enable the Ollama Assistant (Optional)

Install Ollama from [ollama.com/download](https://ollama.com/download), then download the model used by default:

```bash
ollama pull llama3.2:1b
```

Make sure the Ollama service is running. If it is not already running, start it with:

```bash
ollama serve
```

On macOS installations managed by Homebrew, the service can instead be started in the background with:

```bash
brew services start ollama
```

With the FastAPI application running, use the **Ask the directory** form on the dashboard. You can also call the endpoint directly:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How many students are in the directory?"}'
```

The response includes the question, answer, model name, and number of records supplied to the model. If Ollama is unavailable or the model has not been downloaded, the endpoint returns `503`; the student CRUD features continue to work.

### AI Data Handling

The backend retrieves records using regular database queries and sends read-only context to Ollama. The model does not connect to the database or execute SQL. The context includes student names, dates of birth, courses, and enrollment dates; it excludes email addresses, phone numbers, and addresses. At most 200 records are included in one question. Ollama runs locally by default at `http://localhost:11434`.

Optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:1b` | Model tag to use for answers |

## 6. Run the Tests

With the virtual environment active, run:

```bash
python -m pytest -v
```

The tests use a separate `test_students.db` database and mock the AI response; they do not require Ollama to be installed or running.

## Project Structure

```text

project-root/
│
├── app/
│   ├── ai.py             # Ollama prompt construction and local model requests
│   ├── crud.py           # Student database operations
│   ├── database.py       # SQLite engine and database sessions
│   ├── main.py           # FastAPI routes and application setup
│   ├── models.py         # SQLAlchemy student model
│   ├── schemas.py        # Request validation and response schemas
│   │
│   └── static/
│       ├── index.html    # Dashboard interface
│       ├── style.css     # Dashboard styling
│       └── script.js     # Dashboard functionality
│
├── tests/                # Automated API and validation tests
│
├── seed_data.py          # Optional fictional sample records
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation

```
