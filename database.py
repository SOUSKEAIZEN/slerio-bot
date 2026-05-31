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
    
    if not all([host, port, database, user, password]):
        logger.error("Database Connection Failure: One or more database environment variables are missing!")
        raise ValueError("Missing database credentials in .env file.")
        
    try:
        logger.info("Database Connection: Attempting secure connection to host: %s on port: %s...", host, port)
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
        logger.error("Database Connection Failure: Unable to connect to Aiven cloud instance. Error: %s", str(e), exc_info=True)
        raise

def initialize_database():
    """Creates or updates the necessary database tables ensuring schemas are fully unaligned and correct."""
    logger.info("Database Initialization: Starting structural table creation sequence...")
    
    # Drop older conflicting tables to clear out mismatched old column structures completely
    drop_old_tables_query = """
    DROP TABLE IF EXISTS price_history CASCADE;
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS users CASCADE;
    """
    
    create_users_table = """
    CREATE TABLE users (
        telegram_id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_products_table = """
    CREATE TABLE products (
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
    CREATE TABLE price_history (
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
        
        # Check if column conflict exists by executing drop once to sanitize
        logger.info("Database Sanitization: Dropping any old mismatched schema structures...")
        cursor.execute(drop_old_tables_query)
        
        logger.info("Database Initialization: Deploying fresh unified 'users' table...")
        cursor.execute(create_users_table)
        
        logger.info("Database Initialization: Deploying fresh unified 'products' table...")
        cursor.execute(create_products_table)
        
        logger.info("Database Initialization: Deploying fresh unified 'price_history' table...")
        cursor.execute(create_price_history_table)
        
        connection.commit()
        logger.info("Database Initialization: All core unified tables successfully deployed and verified.")
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error("Database Initialization Failure: Structural setup aborted due to error: %s", str(e), exc_info=True)
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def add_product(user_id: int, url: str, name: str, target_price: float, store_type: str) -> bool:
    """Inserts a newly tracked product into the cloud products table."""
    logger.info("Database Operation: Attempting to save product tracking profile for User: %s...", user_id)
    
    insert_query = """
    INSERT INTO products (user_id, product_url, product_name, target_price, store_type)
    VALUES (%s, %s, %s, %s, %s);
    """
    
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(insert_query, (user_id, url, name, target_price, store_type))
        connection.commit()
        logger.info("Database Operation Success: Product '%s' cleanly registered for tracking.", name)
        return True
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error("Database Operation Failure: Could not add product. Error: %s", str(e), exc_info=True)
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_tracked_products(user_id: int) -> list:
    """Retrieves all tracked items registered by a specific Telegram user."""
    logger.info("Database Query: Fetching all active tracked products for User: %s...", user_id)
    
    select_query = """
    SELECT id, product_name, target_price, last_checked_price, store_type, product_url 
    FROM products 
    WHERE user_id = %s 
    ORDER BY created_at DESC;
    """
    
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(select_query, (user_id,))
        rows = cursor.fetchall()
        logger.info("Database Query Success: Retrieved %s tracked items.", len(rows))
        return rows
    except Exception as e:
        logger.error("Database Query Failure: Unable to fetch items. Error: %s", str(e), exc_info=True)
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    print("Running standalone database function verification test...")
    initialize_database()