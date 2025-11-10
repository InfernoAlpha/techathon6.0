import sqlite3
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from schema import data_base_schema,data_fetch_service_schema

if __name__ == "__main__":
    conn = sqlite3.connect("mock_data_services.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price INTEGER,
        location TEXT,
        slot DATE
    )
    """)

    cursor.executemany("INSERT INTO services (name,price,location,slot) VALUES (?,?,?,?)",[
        ("A motors","20000","Hyderabad","2025-11-10"),
        ("B motors","19500","Pune","2025-11-15"),
        ("c motors","18000","Mumbai","2025-11-18")
        ])

    conn.commit()

    cursor.execute("SELECT * FROM services")
    print(cursor.fetchall())
    conn.close()

engine = create_engine("sqlite:///mock_data_services.db")
db = SQLDatabase(engine)

@tool
def fetch_service_data(state:data_fetch_service_schema):
    """
    returns maintanence history from a database based on a key like vehicle model or customer name,
    example: let these be the data in the database
    ("A motors","20000","Hyderabad","2025-11-10"),
    ("B motors","19500","Pune","2025-11-15"),
    ("c motors","18000","Mumbai","2025-11-18")

    they are in the format (name,price,location,slot)

    if the key is name , for example A motors
    the tool returns ("A motors","20000","Hyderabad","2025-11-10")
    """
    print("fetching data")
    query = f"SELECT name,price,location,slot FROM services WHERE {state.model_dump(by_alias=True)['key']} = '{state.model_dump(by_alias=True)['key_value']}'"
    data = db.run(query)
    return data

@tool
def log_service_data(data:data_base_schema):
    """
    log's or inserts the data into the database
    """
    print("loging data")
    insert_query = f"""
    INSERT INTO services (name,price,location,slot)
    VALUES ('{data['name']}','{data['price']}','{data['location']}','{data['slot']}')
    """

    db.run(insert_query)