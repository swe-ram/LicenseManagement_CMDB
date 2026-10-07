from database.database import engine


try:
    with engine.connect() as connection:
        print("================================")
        print("PostgreSQL connection successful!")
        print("================================")

except Exception as e:
    print("================================")
    print("PostgreSQL connection failed!")
    print("================================")
    print(e)