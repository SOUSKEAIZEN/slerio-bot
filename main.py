import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ConversationHandler, 
    ContextTypes, 
    filters
)

# Import our custom logging, database, and scraper modules
from logger import logger
from database import initialize_database, get_db_connection, add_product
from scraper import clean_and_identify_url

# Import the keep-alive background web server module
from keep_alive import keep_alive

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Define Conversation States
AWAITING_TARGET_PRICE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command. Registers users into the cloud database."""
    user = update.effective_user
    logger.info(u"Received /start command from user: %s (ID: %s)", user.username, user.id)
    
    db_connection = None
    db_cursor = None
    try:
        logger.info(u"Database Operation: Registering user %s (ID: %s) into 'users' table...", user.username, user.id)
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        upsert_user_query = """
        INSERT INTO users (telegram_id, username)
        VALUES (%s, %s)
        ON CONFLICT (telegram_id) 
        DO UPDATE SET username = EXCLUDED.username;
        """
        db_cursor.execute(upsert_user_query, (user.id, user.username))
        db_connection.commit()
        logger.info(u"Database Operation Success: User %s (ID: %s) synchronized cleanly.", user.username, user.id)
        
    except Exception as e:
        if db_connection:
            db_connection.rollback()
        logger.error(u"Database Operation Failure: Could not register user %s. Error: %s", user.id, str(e), exc_info=True)
        
    finally:
        if db_cursor:
            db_cursor.close()
        if db_connection:
            db_connection.close()

    welcome_message = (
        u"Hello! I am SLERO, your personal price tracking assistant.\n\n"
        u"Send me a product link from Amazon, Flipkart, Blinkit, or Swiggy Instamart, "
        u"and I will help you monitor its price and send you instant alerts when it drops!"
    )
    await update.message.reply_text(welcome_message)


async def handle_link_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts sent links, validates them, and initiates the price capture sequence."""
    raw_url = update.message.text
    user_id = update.effective_user.id
    logger.info(u"Link Listener: User %s sent a link for processing.", user_id)

    # Clean parameters and identify the target e-commerce store
    parsed_result = clean_and_identify_url(raw_url)
    
    if not parsed_result["is_valid"]:
        logger.warning(u"Link Listener: Link processing rejected for user %s. Invalid/unsupported URL structure.", user_id)
        await update.message.reply_text(
            u"❌ Sorry, that link isn't supported. Please send a valid link from "
            u"Amazon, Flipkart, Blinkit, or Swiggy Instamart."
        )
        return ConversationHandler.END

    # Temporarily store product metadata inside context user data memory strings
    context.user_data["clean_url"] = parsed_result["clean_url"]
    context.user_data["store_type"] = parsed_result["store_type"]
    
    logger.info(u"Link Listener: URL parsed successfully (%s). Transitioning to AWAITING_TARGET_PRICE state.", parsed_result["store_type"])
    
    await update.message.reply_text(
        u"✅ Link recognized!\n"
        u"Platform detected: " + parsed_result["store_type"].upper() + u"\n\n"
        u"Please reply with your target price in INR (e.g., if you want an alert when it drops below 1500, reply with 1500):"
    )
    return AWAITING_TARGET_PRICE


async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validates numerical target price input and commits the profile data to the Aiven Cloud database."""
    price_text = update.message.text.strip()
    user_id = update.effective_user.id
    logger.info(u"Price Listener: User %s submitted price input: '%s'", user_id, price_text)

    try:
        # Validate that the price input string converts to a valid positive float/integer
        target_price = float(price_text)
        if target_price <= 0:
            raise ValueError("Price must be a positive number.")
    except ValueError:
        logger.warning(u"Price Listener: Invalid price format string parsed from user %s.", user_id)
        await update.message.reply_text(u"❌ Invalid price. Please enter a proper positive number (e.g., 499 or 1250.50):")
        return AWAITING_TARGET_PRICE

    # Retrieve cached product parameters out of user data storage frames
    clean_url = context.user_data.get("clean_url")
    store_type = context.user_data.get("store_type")
    
    # Placeholder placeholder name before the scraper background job populates it fully
    placeholder_name = u"Tracked Item (" + store_type.capitalize() + u")"

    logger.info(u"Database Target: Writing tracking profile to Aiven Cloud for User: %s...", user_id)
    
    # Save parameters to the cloud database
    success = add_product(
        user_id=user_id,
        url=clean_url,
        name=placeholder_name,
        target_price=target_price,
        store_type=store_type
    )

    if success:
        logger.info(u"Database Target Success: Tracked product committed cleanly for User: %s.", user_id)
        await update.message.reply_text(
            u"🎉 Setup complete! I am now tracking this item for you.\n\n"
            u"Store: " + store_type.upper() + u"\n"
            u"Target Price: ₹" + str(target_price) + u"\n\n"
            u"I will check the price trends regularly and notify you immediately when it drops below your target!"
        )
    else:
        logger.error(u"Database Target Failure: Cloud pipeline dropped execution save packet for User: %s.", user_id)
        await update.message.reply_text(u"❌ Something went wrong while saving your product tracking profile. Please try again later.")

    # Explicitly clear out context user cache variables to free up environment allocations
    context.user_data.clear()
    logger.info("Conversation Sequence: Flushed memory blocks. Flow state completed successfully.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gracefully aborts any open active setup tracker conversation layers."""
    logger.info(u"Conversation Sequence: User %s triggered manual cancellation rule.", update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(u"Tracking setup cancelled. You can paste a new product link anytime!")
    return ConversationHandler.END


def main():
    logger.info("Starting SLERO Bot execution sequence...")
    
    # Initialize the background Keep-Alive Flask server thread
    logger.info("Deployment Safeguard: Activating Keep-Alive background server pipeline...")
    keep_alive()
    
    if not BOT_TOKEN:
        logger.error("CRITICAL FAILURE: TELEGRAM_BOT_TOKEN not found in environment variables. Execution stopped.")
        return

    try:
        # Initialize Aiven Cloud Schema structures upon startup
        logger.info("Database Initialization: Triggering schema migration checklist...")
        initialize_database()
        logger.info("Database Initialization Sequence: Completed successfully. Core schemas online.")

        logger.info("Initializing Telegram Application Builder...")
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Build out Conversation handling matrices for clean links input structures
        tracking_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.TEXT & (filters.Entity("url") | filters.CaptionEntity("url") | filters.Regex(r"https?://")), handle_link_input)],
            states={
                AWAITING_TARGET_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        
        # Register commands and automated link conversation state matrices
        logger.info("Registering command and conversation handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(tracking_conv_handler)
        
        logger.info("Bot successfully connected! Polling for messages has started...")
        application.run_polling()
        
    except Exception as e:
        logger.error(u"CRITICAL FAILURE during bot execution loop: %s", str(e), exc_info=True)

if __name__ == '__main__':
    main()