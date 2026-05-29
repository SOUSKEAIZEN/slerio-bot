import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Import our custom logging system
from logger import logger

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user = update.effective_user
    logger.info(u"Received /start command from user: %s (ID: %s)", user.username, user.id)
    
    welcome_message = (
        u"Hello! I am SLERO, your personal price tracking assistant.\n\n"
        u"I will help you monitor prices across Amazon, Flipkart, Blinkit, and Instamart. "
        u"Currently, I am setting up my systems. Stay tuned!"
    )
    
    await update.message.reply_text(welcome_message)
    logger.info(u"Sent welcome message to user: %s", user.id)

def main():
    logger.info("Starting SLERO Bot execution sequence...")
    
    if not BOT_TOKEN:
        logger.error("CRITICAL FAILURE: TELEGRAM_BOT_TOKEN not found in environment variables. Execution stopped.")
        return

    try:
        # Build the application using the token
        logger.info("Initializing Telegram Application Builder...")
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Register commands
        logger.info("Registering command handlers...")
        application.add_handler(CommandHandler("start", start))
        
        # Start polling the Telegram servers for updates
        logger.info("Bot successfully connected! Polling for messages has started...")
        application.run_polling()
        
    except Exception as e:
        logger.error(u"CRITICAL FAILURE during bot execution loop: %s", str(e), exc_info=True)

if __name__ == '__main__':
    main()