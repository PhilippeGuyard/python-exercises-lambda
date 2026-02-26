import re
import logging
import os
import random
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI

from topics_list import topics

logger = logging.getLogger(__name__)
load_dotenv()


def send_email(subject, body):
    """Sends an HTML email via Mailgun."""
    mailgun_api_key = os.environ.get("MAILGUN_API_KEY")
    mailgun_domain = os.environ.get("MAILGUN_DOMAIN")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    if not (mailgun_api_key and mailgun_domain and recipient_email):
        logger.error("Missing Mailgun configuration.")
        return

    try:
        response = requests.post(
            f"https://api.eu.mailgun.net/v3/{mailgun_domain}/messages",
            auth=("api", mailgun_api_key),
            data={
                "from": f"Python Exercises <noreply@{mailgun_domain}>",
                "to": recipient_email,
                "subject": subject,
                "html": body,
            },
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Email sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email: {e}")


def send_to_notion(
    topic, cheat_sheet, problem_statement, hints, solution, extensions, tokens_used
):
    """Logs the exercise to Notion."""
    notion_token = os.environ.get("NOTION_API_KEY")
    notion_database_id = os.environ.get("NOTION_DATABASE_ID")

    if not (notion_token and notion_database_id):
        logger.error("Missing Notion API configuration.")
        return

    notion = Client(auth=notion_token)

    try:
        current_date = datetime.now(timezone.utc).isoformat()

        hints_block = [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": hint}}]},
            }
            for hint in hints
        ]
        extensions_block = [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": extension}}]},
            }
            for extension in extensions
        ]

        notion.pages.create(
            parent={"database_id": notion_database_id},
            properties={
                "Name": {"title": [{"text": {"content": topic}}]},
                "Tokens Used": {"number": tokens_used},
                "Date": {"date": {"start": current_date}},
            },
            children=[
                {
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"text": {"content": topic}}]},
                },
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Cheat Sheet"}}]},
                },
                {
                    "type": "code",
                    "code": {
                        "rich_text": [{"text": {"content": cheat_sheet}}],
                        "language": "python",
                    },
                },
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Problem Statement"}}]
                    },
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": problem_statement}}]
                    },
                },
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Hints"}}]},
                },
                *hints_block,
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Solution"}}]},
                },
                {
                    "type": "code",
                    "code": {
                        "rich_text": [{"text": {"content": solution}}],
                        "language": "python",
                    },
                },
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Extensions"}}]},
                },
                *extensions_block,
            ],
        )
        logger.info("Exercise successfully added to Notion.")
    except Exception as e:
        logger.error(f"Error logging data to Notion: {e}")


def generate_prompt_messages(topic):
    """Returns Chat Completions messages for generating a Python exercise."""
    system_message = (
        "You are a helpful assistant dedicated to helping people improve their Python coding skills. "
        "Your task is to create daily exercises for intermediate to advanced developers. "
        "Respond with well-formatted HTML using this exact structure:\n"
        "<h1>Title of the Exercise</h1>\n"
        "<h2>Cheat Sheet</h2>\n"
        "<pre><code>Key syntax and concepts with brief explanations as comments</code></pre>\n"
        "<h2>Problem Statement</h2>\n"
        "<p>A concise description of the problem.</p>\n"
        "<h2>Hints</h2>\n"
        "<ul><li>Hint 1</li><li>Hint 2</li></ul>\n"
        "<h2>Solution</h2>\n"
        "<pre><code>Complete solution code with inline comments</code></pre>\n"
        "<h2>Extensions</h2>\n"
        "<ul><li>Extension idea 1</li><li>Extension idea 2</li></ul>\n"
        "Use proper semantic HTML. Enclose all code in <pre><code> blocks, properly indented."
    )
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Generate a daily Python exercise on the topic: '{topic}'."},
    ]


def parse_openai_response(response_content):
    """Parses the OpenAI HTML response to extract key sections."""
    soup = BeautifulSoup(response_content, "html.parser")

    def find_h2(text):
        return soup.find("h2", string=re.compile(rf"\s*{re.escape(text)}\s*", re.IGNORECASE))

    topic_tag = soup.find("h1")
    topic = topic_tag.get_text(strip=True) if topic_tag else "Python Exercise"

    cheat_sheet_pre = soup.find("pre")
    cheat_sheet = cheat_sheet_pre.get_text(strip=True) if cheat_sheet_pre else "No cheat sheet available."

    problem_h2 = find_h2("Problem Statement")
    problem_p = problem_h2.find_next("p") if problem_h2 else None
    problem_statement = problem_p.get_text(strip=True) if problem_p else "No problem statement available."

    hints_h2 = find_h2("Hints")
    hints_ul = hints_h2.find_next("ul") if hints_h2 else None
    hints = [li.get_text(strip=True) for li in hints_ul.find_all("li")] if hints_ul else []

    solution_h2 = find_h2("Solution")
    solution_pre = solution_h2.find_next("pre") if solution_h2 else None
    solution = solution_pre.get_text(strip=True) if solution_pre else "No solution available."

    extensions_h2 = find_h2("Extensions")
    extensions_ul = extensions_h2.find_next("ul") if extensions_h2 else None
    extensions = [li.get_text(strip=True) for li in extensions_ul.find_all("li")] if extensions_ul else []

    return topic, cheat_sheet, problem_statement, hints, solution, extensions


def generate_email_html(
    topic, cheat_sheet, problem_statement, hints, solution, extensions, date, tokens_used
):
    """Generates styled HTML for the exercise email."""
    hints_html = "".join(f"<li>{hint}</li>" for hint in hints)
    extensions_html = "".join(f"<li>{extension}</li>" for extension in extensions)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background: #fff;
            border-radius: 8px;
            padding: 32px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        h1 {{
            font-size: 1.6em;
            color: #1a1a2e;
            border-bottom: 3px solid #4f8ef7;
            padding-bottom: 8px;
        }}
        h2 {{
            font-size: 1.1em;
            color: #4f8ef7;
            margin-top: 28px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        pre {{
            background: #1e1e2e;
            color: #cdd6f4;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        code {{
            font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace;
        }}
        p {{
            line-height: 1.7;
        }}
        ul {{
            padding-left: 20px;
            line-height: 1.8;
        }}
        li {{
            margin-bottom: 4px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #eee;
            font-size: 0.8em;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{topic}</h1>

        <h2>Cheat Sheet</h2>
        <pre><code>{cheat_sheet}</code></pre>

        <h2>Problem Statement</h2>
        <p>{problem_statement}</p>

        <h2>Hints</h2>
        <ul>{hints_html}</ul>

        <h2>Solution</h2>
        <pre><code>{solution}</code></pre>

        <h2>Extensions</h2>
        <ul>{extensions_html}</ul>

        <div class="footer">
            <p>Generated on {date} &nbsp;|&nbsp; Tokens used: {tokens_used}</p>
        </div>
    </div>
</body>
</html>"""


def lambda_handler(event, context):
    """AWS Lambda handler: generates a Python exercise, emails it, and logs it to Notion."""
    logger.info("Scheduled task started.")

    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY.")

        topic = random.choice(topics)
        logger.info(f"Selected topic: {topic}")

        client = OpenAI(api_key=api_key)
        messages = generate_prompt_messages(topic)

        logger.info("Sending prompt to OpenAI.")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            timeout=60,
        )

        response_content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        logger.info(f"OpenAI response received. Tokens used: {tokens_used}")

        topic, cheat_sheet, problem_statement, hints, solution, extensions = (
            parse_openai_response(response_content)
        )

        date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        email_html = generate_email_html(
            topic, cheat_sheet, problem_statement, hints, solution, extensions, date, tokens_used
        )

        send_email(f"Python Exercise: {topic}", email_html)
        send_to_notion(
            topic, cheat_sheet, problem_statement, hints, solution, extensions, tokens_used
        )

        return {
            "statusCode": 200,
            "body": "Email sent and exercise logged to Notion successfully.",
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"statusCode": 500, "body": str(e)}


if __name__ == "__main__":
    lambda_handler(None, None)
