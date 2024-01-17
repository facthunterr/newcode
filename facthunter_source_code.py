import os
from googleapiclient.discovery import build
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
import google.generativeai as genai
import datetime

# Telegram bot token
TELEGRAM_TOKEN = 'your_telegram_token_here'
# Google API credentials
GOOGLE_API_KEY = 'your_google_api_key_here'
FACT_CHECK_API_VERSION = 'v1alpha1'
FACT_CHECK_API_SERVICE_NAME = 'factchecktools'
GOOGLEE_API_KEY = 'your_generative_ai_google_api_key_here'
genai.configure(api_key=GOOGLEE_API_KEY)

# Define a file path for the log file
LOG_FILE_PATH = "user_logs.txt"

def check_fact_check_explorer(claim: str) -> str:
    service = build(FACT_CHECK_API_SERVICE_NAME, FACT_CHECK_API_VERSION, developerKey=GOOGLE_API_KEY)

    try:
        # Use the claim as the query to Fact Check Explorer API
        request = service.claims().search(query=claim)
        response = request.execute()

        # Check if any results are found
        if 'claims' in response:
            claims = response['claims']
            if claims:
                # Get the first claim and check its claimReview
                claim_review = claims[0].get('claimReview', [])
                if claim_review:
                    # Check the claim's claimReview for the result
                    result = claim_review[0].get('text', 'Result not available.')
                    publication_date = claim_review[0].get('publishDate', 'Date not available.')
                    url = claim_review[0].get('url', 'URL not available.')
                    response_message = f"\nClaim: {claim}\nURL: {url}"

                    return response_message

        # If no results are found, provide an appropriate response
        return 'No results found for the claim.'

    except Exception as e:
        print(f"An error occurred in fact-checking: {e}")
        return 'Error occurred while fact-checking.'

def verify_claim_generative(claim):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(claim)
        # Process the response and return the verification result
        generated_text = response.text
        print(generated_text)
        return generated_text

    except Exception as e:
        print(f"An error occurred in generative model: {e}")
        return 'Error occurred while processing the claim with the generative model.'

def log_user_input(username, claim, verification_result):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - User: {username}, Claim: {claim}, Verification: {verification_result}\n"

    # Append the log entry to the log file
    with open(LOG_FILE_PATH, "a") as log_file:
        log_file.write(log_entry)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Send a claim to have it verified.')

def verify_claim(update: Update, context: CallbackContext):
    claim = update.message.text
    username = update.message.from_user.username  # Get the username
    is_claim_true = verify_claim_generative(claim)

    # Log the user input
    log_user_input(username, claim, is_claim_true)

    # Reply to the user with the claim and its verification result
    update.message.reply_text(f'Claim: {claim}, Verification: {is_claim_true}')

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, verify_claim))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
