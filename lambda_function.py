from notion_client import Client
from bs4 import BeautifulSoup
import logging
import os
import random
from openai import OpenAI
from dotenv import load_dotenv
from topics_list import topics
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)
load_dotenv()


def send_email(subject, body):
    """
    Sends an email using the Mailgun API.
    """
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
        )
        response.raise_for_status()
        logger.info("Email sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email: {e}")


def send_to_notion(
    topic, cheat_sheet, problem_statement, hints, solution, extensions, tokens_used
):
    """
    Logs the exercise to Notion.
    """
    notion_token = os.environ.get("NOTION_API_KEY")
    notion_database_id = os.environ.get("NOTION_DATABASE_ID")

    if not (notion_token and notion_database_id):
        logger.error("Missing Notion API configuration.")
        return

    notion = Client(auth=notion_token)

    try:
        # Add current date
        current_date = datetime.now(timezone.utc).isoformat()

        # Prepare Notion blocks
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

        # Create Notion page
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


def generate_detailed_prompt(topic):
    """
    Generates a detailed prompt for OpenAI based on the selected topic.
    """
    return (
        f"You are a helpful assistant dedicated to helping people improve their Python coding skills. "
        f"Today's topic is '{topic}'. "
        "Your task is to create a daily exercise for intermediate to advanced developers to sharpen their skills. The response must be a well-formatted "
        "HTML email structured as follows:"
        "<h1>Title of the Exercise</h1>"
        "<h2>Cheat Sheet</h2>"
        "<pre><code>Code snippets with explanations</code></pre>"
        "<h2>Problem Statement</h2>"
        "A concise description of the problem in words."
        "<h2>Hints</h2>"
        "Bullet points providing guidance."
        "<h2>Solution</h2>"
        "<pre><code>Complete solution code with comments</code></pre>"
        "<h2>Extensions</h2>"
        "Ideas for expanding upon the learned concepts."
        "Ensure the HTML is clean and uses proper semantic tags. All code should be enclosed in <pre><code> blocks, properly indented."
    )


def parse_openai_response(response_content):
    """
    Parses the OpenAI HTML response to extract key sections.
    """
    soup = BeautifulSoup(response_content, "html.parser")

    # Extract sections
    topic = soup.find("h1").text if soup.find("h1") else "Python Exercise"
    cheat_sheet = (
        soup.find("pre").text if soup.find("pre") else "No cheat sheet available."
    )
    problem_statement = soup.find("h2", text="Problem Statement").find_next("p").text
    hints = [
        li.text for li in soup.find("h2", text="Hints").find_next("ul").find_all("li")
    ]
    solution = soup.find("h2", text="Solution").find_next("pre").text
    extensions = [
        li.text
        for li in soup.find("h2", text="Extensions").find_next("ul").find_all("li")
    ]

    return topic, cheat_sheet, problem_statement, hints, solution, extensions


def generate_email_html(
    topic, cheat_sheet, problem_statement, hints, solution, extensions, date, tokens_used
):
    """
    Generates formatted HTML for the email.
    """
    hints_html = "".join(f"<li>{hint}</li>" for hint in hints)
    extensions_html = "".join(f"<li>{extension}</li>" for extension in extensions)

    email_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{topic}</title>
        <style>
            /* CSS as before */
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
                <p>Generated on {date}</p>
                <p>Tokens Used: {tokens_used}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return email_html


def lambda_handler(event, context):
    """
    AWS Lambda handler to generate OpenAI response, send it via email, and log it to Notion.
    """
    logger.info("Scheduled task started.")

    try:
        # Load environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        assistant_id = os.environ.get("OPENAI_ASSISTANT_ID")

        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY.")
        if not assistant_id:
            raise ValueError("Missing OPENAI_ASSISTANT_ID.")

        # Select a random topic
        topic = random.choice(topics)
        logger.info(f"Selected topic: {topic}")

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Generate detailed prompt
        prompt = generate_detailed_prompt(topic)

        # Interact with OpenAI
        logger.info("Sending prompt to OpenAI.")
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=prompt
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions="Generate a detailed exercise based on the prompt.",
        )

        if run.status != "completed":
            logger.error(f"OpenAI response generation failed. Status: {run.status}")
            return {"statusCode": 500, "body": "Failed to generate response."}

        # Retrieve OpenAI response
        logger.info("Fetching OpenAI response.")
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_content = messages.data[0].content[0].text.value
        tokens_used = run.usage.total_tokens

        # Parse OpenAI response
        topic, cheat_sheet, problem_statement, hints, solution, extensions = (
            parse_openai_response(response_content)
        )

        # Generate email HTML
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        email_html = generate_email_html(
            topic,
            cheat_sheet,
            problem_statement,
            hints,
            solution,
            extensions,
            date,
            tokens_used,
        )

        # Send email
        send_email(f"Python Exercise: {topic}", email_html)

        # Log to Notion
        send_to_notion(
            topic,
            cheat_sheet,
            problem_statement,
            hints,
            solution,
            extensions,
            tokens_used,
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
