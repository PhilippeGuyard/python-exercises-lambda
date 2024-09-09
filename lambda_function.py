import json
import logging
import os

import requests
from dotenv import load_dotenv
from openai import OpenAI

# Set up logging
logger = logging.getLogger()
logger.setLevel("INFO")

load_dotenv()


def send_email(subject, body):
    mailgun_api_key = os.environ["MAILGUN_API_KEY"]
    mailgun_domain = os.environ["MAILGUN_DOMAIN"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]

    try:
        result = requests.post(
            f"https://api.eu.mailgun.net/v3/{mailgun_domain}/messages",
            auth=("api", mailgun_api_key),
            data={
                "from": f"Your daily Python exercise <noreply@{mailgun_domain}>",
                "to": recipient_email,
                "subject": subject,
                "html": body,
            },
        )
        result.raise_for_status()
        logger.info("Email sent successfully")
    except requests.exceptions.RequestException as e:
        logger.error("Error sending email via Mailgun: %s", e)


def lambda_handler(event, context):
    logger.info("Scheduled task started.")

    try:
        # Create OpenAI client and make a request
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a helpful assistant dedicated to helping people improve their Python coding skills. "
                        "The way you operate is by emailing daily exercises focused on a single topic. Your audience is advanced "
                        "developers wanting to brush up on their skills. Your emails are structured in this way:"
                        "1) Title"
                        "2) A cheat sheet summary of the principles at play. For example, if dealing with list comprehensions, "
                        "you will give a few examples of generic list comprehensions. You will add brief code comments but no "
                        "other text at this point. However all the elements needed to solve the problem must be present in your examples."
                        "3) Problem statement in words: this is the problem that the users will need to solve."
                        "4) A few hints as to how to solve the problem"
                        "5) The solution to the problem"
                        "6) Possible extensions to what was learned."
                        "Your final output will be HTML, with code examples formatted as such."
                        "Make sure you include the title, cheat sheet, problem statement, hints, solution, and extensions."
                        "Also make sure your problems are aimed at an advanced audience."
                        "And make sure your email is formatted correctly."
                    ),
                },
            ],
        )

        openai_result = response.choices[0].message.content.strip()
        logger.info("OpenAI response received")

        # Send the results via email
        send_email("Automated OpenAI Task Result", openai_result)

    except Exception as e:
        logger.error("Error processing: %s", e)
        error_message = f"Error processing the request: {e}"
        send_email("OpenAI Task Processing Failed", error_message)
        return {
            "statusCode": 500,
            "body": json.dumps(error_message),
        }

    return {"statusCode": 200, "body": json.dumps("Email sent successfully")}
