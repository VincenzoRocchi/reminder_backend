import mysql.connector

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='test-database-reminder-backend.cteiosm4sgwc.eu-central-1.rds.amazonaws.com',
            port=3306,
            user='admin',
            password='v4Bw^ev&$CG&mwy8vFg^',
            database='test-database-reminder-backend'  # Replace with your actual database name
        )
        if connection.is_connected():
            print("Successfully connected to the database")
            connection.ping(reconnect=True, attempts=3, delay=5)
            print("Ping successful")
            return connection
        else:
            print("Failed to connect to the database")
            return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def main():
    connection = connect_to_database()
    if connection:
        connection.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()
