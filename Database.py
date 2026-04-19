# import psycopg2
# from typing import Optional

# def connect_to_database() -> Optional[psycopg2.extensions.connection]:
#     """
#     Simple function to connect to PostgreSQL database.
#     """
#     try:
#         # Connect to PostgreSQL database
#         connection = psycopg2.connect(
#             host="localhost",
#             port="5433",
#             database="BankData",
#             user="postgres",
#             password="9522"
#         )
#         print("Connected to PostgreSQL database!")
#         return connection
#     except Exception as error:
#         print("Error connecting to PostgreSQL database:", error)
#         return None

# # Test the connection
# if __name__ == "__main__":
#     conn = connect_to_database()
#     if conn:
#         conn.close()
#         print("Connection closed.")



import psycopg2
from typing import Optional
 
# Neon DB Connection String
DATABASE_URL = "postgresql://neondb_owner:npg_iRe8tla3xdfn@ep-tiny-tooth-a1d04ct7-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
 
def connect_to_database() -> Optional[psycopg2.extensions.connection]:
    """
    Connect to Neon PostgreSQL database using connection string.
    """
    try:
        connection = psycopg2.connect(DATABASE_URL)
        print("Connected to Neon database!")
        return connection
    except Exception as error:
        print("Error connecting to Neon database:", error)
        return None
 
# Test the connection
if __name__ == "__main__":
    conn = connect_to_database()
    if conn:
        conn.close()
        print("Connection closed.")
 