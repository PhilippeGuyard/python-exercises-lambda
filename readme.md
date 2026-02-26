# Python Exercises Lambda

> A serverless daily Python exercise generator — picks a random topic, generates a structured exercise with GPT-4o, emails it, and logs it to Notion. Fully automated via AWS Lambda and GitHub Actions.

---

## How It Works

Each day, the Lambda function:

1. Picks a random topic from a curated list of 254 Python subjects
2. Sends a structured prompt to OpenAI's Chat Completions API
3. Parses the HTML response into exercise sections
4. Emails the formatted exercise via Mailgun
5. Logs the exercise (with token usage) to a Notion database

```
AWS EventBridge (schedule)
        │
        ▼
  AWS Lambda (Python 3.12)
        │
        ├──► OpenAI Chat Completions (GPT-4o)
        │         │
        │         ▼
        │    Parse HTML response
        │         │
        ├─────────┼──► Mailgun  ──► Email inbox
        │         │
        └─────────┴──► Notion   ──► Exercise database
```

Each exercise includes:
- **Cheat Sheet** — key syntax and concepts
- **Problem Statement** — a concrete coding challenge
- **Hints** — progressive guidance without spoilers
- **Solution** — complete, commented code
- **Extensions** — ideas for going deeper

---

## Prerequisites

- Python 3.12+
- AWS account with a Lambda function named `PythonExercises` (region `eu-west-2`)
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Mailgun account](https://www.mailgun.com/) (EU region)
- [Notion integration](https://www.notion.so/my-integrations) with a database containing `Name` (title), `Date` (date), and `Tokens Used` (number) properties

---

## Local Development

```bash
# Clone and set up a virtual environment
git clone https://github.com/your-username/python-exercises-lambda.git
cd python-exercises-lambda
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally
python lambda_function.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `MAILGUN_API_KEY` | Mailgun API key |
| `MAILGUN_DOMAIN` | Your Mailgun sending domain (e.g. `mg.yourdomain.com`) |
| `RECIPIENT_EMAIL` | Email address to receive exercises |
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_DATABASE_ID` | ID of the Notion database for logging |

In production these are set as **Lambda environment variables** — never committed to the repository.

Create a local `.env` file for development (already in `.gitignore`):

```bash
OPENAI_API_KEY=sk-...
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=mg.yourdomain.com
RECIPIENT_EMAIL=you@example.com
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=...
```

---

## Deployment

Deployment is fully automated via GitHub Actions on every push to `main`.

**Pipeline steps:**
1. Lint with flake8
2. Install dependencies into a `package/` directory
3. Zip `lambda_function.py`, `topics_list.py`, and all dependencies
4. Deploy the zip to AWS Lambda using `aws lambda update-function-code`

**Required GitHub secrets:**

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key with `lambda:UpdateFunctionCode` permission |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret key |

### Manual packaging (Docker)

If you need to build the deployment package locally:

```bash
docker build -t lambda-package .
docker run --name lambda-container lambda-package
docker cp lambda-container:/lambda_function.zip ./lambda_function.zip
docker rm lambda-container
```

---

## Exercise Topics

The generator draws from **254 curated Python topics** spanning:

| Level | Examples |
|---|---|
| Core language | List comprehensions, decorators, generators, context managers |
| Concurrency | asyncio, threading, multiprocessing, the GIL |
| Architecture | Design patterns, SOLID principles, clean architecture |
| Data & I/O | File handling, CSV/JSON, SQLite, REST APIs |
| Testing | pytest, mocking, TDD, property-based testing |
| Advanced | Metaclasses, bytecode, C extensions, memory management |
| Ecosystem | FastAPI, SQLAlchemy, Celery, Docker, AWS Lambda |

See [`topics_list.py`](topics_list.py) for the full list.

---

## Project Structure

```
python-exercises-lambda/
├── lambda_function.py      # Core Lambda handler and all application logic
├── topics_list.py          # 254 curated Python exercise topics
├── requirements.txt        # Pinned Python dependencies
├── Dockerfile              # Builds the Lambda deployment zip
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline
└── .env.example            # Template for local environment variables
```

---

## Contributing

Contributions welcome — especially new exercise topics.

1. Fork the repository
2. Add topics to `topics_list.py` (keep alphabetical order within categories)
3. Open a pull request with a brief description

For code changes, please run `flake8` before submitting:

```bash
pip install flake8
flake8 lambda_function.py topics_list.py
```
