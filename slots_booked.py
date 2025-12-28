import sqlite3
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from schema import data_fetch_slots,data_log_slots

if __name__ == "__main__":
    conn = sqlite3.connect("slots_booked.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY,
        customer_name TEXT,
        garage_name TEXT,
        price INTEGER,
        location TEXT,           
        slot DATE
    )
    """)

    cursor.executemany("INSERT INTO slots (customer_name,garage_name,price,location,slot) VALUES (?,?,?,?,?)",[
        ("Z","A motors","20000","Hyderabad","2025-11-10"),
        ("X","B motors","19500","Pune","2025-11-15"),
        ("Y","c motors","18000","Mumbai","2025-11-18")
        ])

    conn.commit()

    cursor.execute("SELECT * FROM slots")
    print(cursor.fetchall())
    conn.close()

engine = create_engine("sqlite:///slots_booked.db")
db = SQLDatabase(engine)

@tool
def fetch_slots_booked_data(state:data_fetch_slots):
    """
    returns maintanence history from a database based on a key like vehicle model or customer name,
    example: let these be the data in the database
    ("Z","A motors","20000","Hyderabad","2025-11-10"),
    ("X","B motors","19500","Pune","2025-11-15"),
    ("Y","c motors","18000","Mumbai","2025-11-18")

    they are in the format (customer_name,garage_name,price,location,slot)

    if the key is garage_name , for example A motors
    the tool returns ("Z","A motors","20000","Hyderabad","2025-11-10")
    """
    print("fetching data")
    query = f"SELECT customer_name,garage_name,price,location,slot FROM slots WHERE {state.model_dump(by_alias=True)['key']} = '{state.model_dump(by_alias=True)['key_value']}'"
    data = db.run(query)
    return data

@tool
def log_slots_booked_data(data:data_log_slots):
    """
    log's or books a specified slot in a specified garage based on the given details
    """
    print("booking slots")
    data = data.model_dump()
    insert_query = f"""
    INSERT INTO slots (customer_name,garage_name,price,location,slot)
    VALUES ('{data['customer_name']}','{data['garage_name']}','{data['price']}','{data['location']}','{data['slot']}')
    """

    db.run(insert_query)
    return "slot has been booked"