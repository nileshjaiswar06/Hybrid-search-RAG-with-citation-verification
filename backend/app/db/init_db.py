from sqlalchemy import text

from app.db.database import engine

def initialize_database() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")