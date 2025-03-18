import mysql.connector

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='test-database-reminder-backend.cteiosm4sgwc.eu-central-1.rds.amazonaws.com',
            user='admin',
            password='v4Bw^ev&$CG&mwy8vFg^',
            database='your-database-name'  # Replace with your actual database name
        )
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
        else:
            print("Failed to connect to the database")
            return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255)
            )
        """)
        connection.commit()  # Important: Commit the changes
        print("Table 'test_table' created successfully (or already existed).")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")

def main():
    connection = connect_to_database()
    if connection:
        try:
            create_table(connection)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":
    main()