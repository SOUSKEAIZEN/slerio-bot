import os
import psycopg2
from dotenv import load_dotenv

# Import our custom logging system
from logger import logger

# Load environment variables
load_dotenv()

def get_db_connection():
    """Establishes and returns a connection to the Aiven PostgreSQL database."""
    logger.info("Database Connection: Retrieving credentials from environment variables...")
    
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    
    # Pre-connection validation log
    if not all([host, port, database, user, password]):
        logger.error("Database Connection Failure: One or more database environment variables are missing!")
        raise ValueError("Missing database credentials in .env file.")
        
    try:
        logger.info(u"Database Connection: Attempting secure connection to host: %s on port: %s...", host, port)
        
        # Establishing connection with SSL requirement enforced by Aiven
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode="require"
        )
        
        logger.info("Database Connection: Handshake successful! Connection established.")
        return connection
        
    except Exception as e:
        logger.error(u"Database Connection Failure: Unable to connect to Aiven cloud instance. Error: %s", str(e), exc_info=True)
        raise

def initialize_database():
    """Creates the necessary database tables if they do not exist."""
    logger.info("Database Initialization: Starting structural table creation sequence...")
    
    # SQL Queries to build out the tracking system architecture
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        telegram_id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
        product_url TEXT NOT NULL,
        product_name TEXT,
        target_price NUMERIC(10, 2),
        last_checked_price NUMERIC(10, 2),
        store_type VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_price_history_table = """
    CREATE TABLE IF NOT EXISTS price_history (
        id SERIAL PRIMARY KEY,
        product_id INT REFERENCES products(id) ON DELETE CASCADE,
        price NUMERIC(10, 2) NOT NULL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Step 1: Create Users Table
        logger.info("Database Initialization: Executing query for 'users' table...")
        cursor.execute(create_users_table)
        logger.info("Database Initialization: 'users' table verified/created successfully.")
        
        # Step 2: Create Products Table
        logger.info("Database Initialization: Executing query for 'products' table...")
        cursor.execute(create_products_table)
        logger.info("Database Initialization: 'products' table verified/created successfully.")
        
        # Step 3: Create Price History Table
        logger.info("Database Initialization: Executing query for 'price_history' table...")
        cursor.execute(create_price_history_table)
        logger.info("Database Initialization: 'price_history' table verified/created successfully.")
        
        # Commit transaction to make changes permanent in the cloud
        logger.info("Database Initialization: Committing changes to cloud instance...")
        connection.commit()
        logger.info("Database Initialization: All core tables successfully deployed and verified.")
        
    except Exception as e:
        if connection:
            logger.warning("Database Initialization Warning: Exception encountered. Rolling back changes...")
            connection.rollback()
        logger.error(u"Database Initialization Failure: Structural setup aborted due to error: %s", str(e), exc_info=True)
        raise
        
    finally:
        if cursor:
            cursor.close()
            logger.info("Database Initialization: Cursor channel closed safely.")
        if connection:
            connection.close()
            logger.info("Database Initialization: Connection channel closed safely.")

if __name__ == "__main__":
    # Allows direct testing of database connection by running 'python database.py'
    print("Running standalone database initialization test...")
    initialize_database()