from sqlalchemy import MetaData, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from model import *

# Create a configured "Session" class
session = Session()

# Initialize MetaData object
metadata = MetaData()

# Bind the metadata to the engine
metadata.reflect(bind=engine)

def truncate_tables():
    try:
        # List of tables to exclude from truncation
        exclude_tables = ['users']

        # Iterate through all the tables in the metadata and truncate them
        for table in reversed(metadata.sorted_tables):
            if table.name not in exclude_tables:
                print(f'Truncating table {table.name}...')
                session.execute(text(f'TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE;'))

        # Commit the changes
        session.commit()
        print('Tables truncated successfully, except for {}.'.format(exclude_tables))

    except SQLAlchemyError as e:
        print(f"Error truncating tables: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    truncate_tables()