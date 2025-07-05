# scripts/setup_db.py

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.config_loader import get_settings
from loguru import logger

settings = get_settings()

def create_sqlite_database():
    """
    Create SQLite database with required tables
    """
    try:
        db_path = settings.DATABASE_URL or "phone_assistant.db"
        
        # Remove sqlite:/// prefix if present
        if db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "")
        
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                source TEXT DEFAULT 'phone_call_assistant'
            )
        ''')
        
        # Create appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                external_id TEXT,
                service_type TEXT NOT NULL,
                title TEXT,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                scheduling_backend TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Create calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                direction TEXT,
                caller_number TEXT,
                called_number TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                status TEXT,
                transcript TEXT,
                summary TEXT,
                sentiment TEXT,
                voice_ai_platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Create services table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                duration INTEGER NOT NULL,
                price DECIMAL(10, 2),
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create automation_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                automation_backend TEXT NOT NULL,
                payload TEXT,
                response TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                appointment_id INTEGER,
                customer_id INTEGER,
                call_id TEXT,
                FOREIGN KEY (appointment_id) REFERENCES appointments (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers (phone)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_appointments_customer_id ON appointments (customer_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON appointments (start_time)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls (call_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_calls_customer_id ON calls (customer_id)
        ''')
        
        # Insert default services
        default_services = [
            ("Consultation", "Initial consultation session", 60, 100.00),
            ("Therapy Session", "Individual therapy session", 60, 150.00),
            ("Group Session", "Group therapy session", 90, 75.00),
            ("Assessment", "Psychological assessment", 120, 200.00),
            ("Follow-up", "Follow-up appointment", 30, 50.00)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO services (name, description, duration, price)
            VALUES (?, ?, ?, ?)
        ''', default_services)
        
        # Commit changes
        conn.commit()
        
        logger.info(f"SQLite database created successfully at: {db_path}")
        
        # Display table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[table[0] for table in tables]}")
        
        # Close connection
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating SQLite database: {str(e)}")
        return False

def create_postgresql_database():
    """
    Create PostgreSQL database with required tables
    """
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Parse database URL
        db_url = settings.DATABASE_URL
        
        # Extract connection parameters
        # Format: postgresql://user:password@host:port/database
        url_parts = db_url.replace("postgresql://", "").split("/")
        db_name = url_parts[1] if len(url_parts) > 1 else "phone_assistant"
        
        auth_host = url_parts[0].split("@")
        host_port = auth_host[1] if len(auth_host) > 1 else "localhost:5432"
        auth = auth_host[0] if len(auth_host) > 1 else "postgres:postgres"
        
        user_pass = auth.split(":")
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        
        host_port_parts = host_port.split(":")
        host = host_port_parts[0]
        port = int(host_port_parts[1]) if len(host_port_parts) > 1 else 5432
        
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name};")
            logger.info(f"Created database: {db_name}")
        
        # Close connection to postgres database
        conn.close()
        
        # Connect to the new database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # Create customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20) UNIQUE,
                email VARCHAR(255) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                source VARCHAR(100) DEFAULT 'phone_call_assistant'
            )
        ''')
        
        # Create appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                external_id VARCHAR(255),
                service_type VARCHAR(100) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                status VARCHAR(50) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                scheduling_backend VARCHAR(50)
            )
        ''')
        
        # Create calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id SERIAL PRIMARY KEY,
                call_id VARCHAR(255) UNIQUE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                direction VARCHAR(20),
                caller_number VARCHAR(20),
                called_number VARCHAR(20),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                status VARCHAR(50),
                transcript TEXT,
                summary TEXT,
                sentiment VARCHAR(20),
                voice_ai_platform VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create services table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                duration INTEGER NOT NULL,
                price DECIMAL(10, 2),
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create automation_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_logs (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                automation_backend VARCHAR(50) NOT NULL,
                payload TEXT,
                response TEXT,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                appointment_id INTEGER REFERENCES appointments(id),
                customer_id INTEGER REFERENCES customers(id),
                call_id VARCHAR(255)
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers (phone)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_appointments_customer_id ON appointments (customer_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON appointments (start_time)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls (call_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_calls_customer_id ON calls (customer_id)
        ''')
        
        # Insert default services
        default_services = [
            ("Consultation", "Initial consultation session", 60, 100.00),
            ("Therapy Session", "Individual therapy session", 60, 150.00),
            ("Group Session", "Group therapy session", 90, 75.00),
            ("Assessment", "Psychological assessment", 120, 200.00),
            ("Follow-up", "Follow-up appointment", 30, 50.00)
        ]
        
        for service in default_services:
            cursor.execute('''
                INSERT INTO services (name, description, duration, price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', service)
        
        # Commit changes
        conn.commit()
        
        logger.info(f"PostgreSQL database setup completed for: {db_name}")
        
        # Display table info
        cursor.execute('''
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        ''')
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[table[0] for table in tables]}")
        
        # Close connection
        conn.close()
        
        return True
        
    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Error creating PostgreSQL database: {str(e)}")
        return False

def setup_database():
    """
    Setup database based on configuration
    """
    try:
        logger.info("Setting up database...")
        
        db_url = settings.DATABASE_URL or "sqlite:///phone_assistant.db"
        
        if db_url.startswith("sqlite"):
            return create_sqlite_database()
        elif db_url.startswith("postgresql"):
            return create_postgresql_database()
        else:
            logger.error(f"Unsupported database type: {db_url}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

def reset_database():
    """
    Reset database by dropping all tables and recreating them
    """
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        db_url = settings.DATABASE_URL or "sqlite:///phone_assistant.db"
        
        if db_url.startswith("sqlite"):
            # For SQLite, just delete the file
            db_path = db_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                os.remove(db_path)
                logger.info(f"Deleted SQLite database: {db_path}")
            
            return create_sqlite_database()
            
        elif db_url.startswith("postgresql"):
            # For PostgreSQL, drop and recreate tables
            import psycopg2
            
            # Parse database URL (simplified)
            url_parts = db_url.replace("postgresql://", "").split("/")
            db_name = url_parts[1] if len(url_parts) > 1 else "phone_assistant"
            
            # Connect and drop tables
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            tables = ["automation_logs", "calls", "appointments", "services", "customers"]
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
            conn.commit()
            conn.close()
            
            logger.info("Dropped all PostgreSQL tables")
            
            return create_postgresql_database()
            
        else:
            logger.error(f"Unsupported database type: {db_url}")
            return False
            
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

def main():
    """
    Main function to handle command line arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup database for Phone Call Assistant")
    parser.add_argument("--reset", action="store_true", help="Reset database (WARNING: deletes all data)")
    parser.add_argument("--create", action="store_true", help="Create database and tables")
    
    args = parser.parse_args()
    
    if args.reset:
        if input("Are you sure you want to reset the database? (y/N): ").lower() == 'y':
            success = reset_database()
        else:
            logger.info("Database reset cancelled")
            return
    elif args.create:
        success = setup_database()
    else:
        # Default action is to create
        success = setup_database()
    
    if success:
        logger.info("Database setup completed successfully!")
    else:
        logger.error("Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()