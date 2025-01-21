import logging
import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv

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
        logger.error("Missing Mailgun configuration in environment variables.")
        return

    try:
        response = requests.post(
            f"https://api.eu.mailgun.net/v3/{mailgun_domain}/messages",
            auth=("api", mailgun_api_key),
            data={
                "from": f"Your daily Python exercise <noreply@{mailgun_domain}>",
                "to": recipient_email,
                "subject": subject,
                "html": body,
            },
        )
        response.raise_for_status()
        logger.info("Email sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email via Mailgun: {e}")


def generate_openai_prompt():
    """
    Generates the prompt to be sent to OpenAI.
    """
    return (
        "You are a helpful assistant dedicated to helping people improve their Python coding skills. "
        "Your task is to create daily exercises for advanced developers to sharpen their skills. The response must be a well-formatted "
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


def lambda_handler(event, context):
    """
    AWS Lambda handler to generate OpenAI response and send it via email.
    """
    logger.info("Scheduled task started.")

    try:
        # Load environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        assistant_id = os.environ.get("OPENAI_ASSISTANT_ID")

        if not api_key:
            raise ValueError(
                "Missing OPENAI_API_KEY. Please set it in the environment variables."
            )
        if not assistant_id:
            raise ValueError(
                "Missing OPENAI_ASSISTANT_ID. Please set it in the environment variables."
            )

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Generate prompt
        prompt = generate_openai_prompt()

        # Create thread and send prompt to OpenAI
        logger.info("Sending prompt to OpenAI.")
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions="Generate the response based on the provided instructions.",
        )

        if run.status != "completed":
            logger.error(f"OpenAI response generation failed. Status: {run.status}")
            return {
                "statusCode": 500,
                "body": json.dumps("Failed to generate response."),
            }

        # Retrieve response
        logger.info("Fetching OpenAI response.")
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_content = messages.data[0].content[0].text.value

        # Log API usage
        tokens_used = run.usage.total_tokens
        logger.info(f"OpenAI usage: {tokens_used} tokens used.")

        # Append usage to email body
        response_with_usage = (
            f"{response_content}<br><br><strong>Tokens Used:</strong> {tokens_used}"
        )

        # Send email
        send_email("Your Daily Python Exercise", response_with_usage)

        return {"statusCode": 200, "body": json.dumps("Email sent successfully.")}

    except Exception as e:
        logger.error(f"Error processing task: {e}")
        send_email("OpenAI Task Processing Failed", f"Error: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {e}")}
