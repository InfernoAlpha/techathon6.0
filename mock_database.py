import sqlite3
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from schema import data_base_schema,data_fetch_schema

if __name__ == "__main__":
    conn = sqlite3.connect("mock_data.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        model TEXT,
        problem TEXT,
        date DATE
    )
    """)

    cursor.executemany("INSERT INTO users (name, email,model,problem,date) VALUES (?,?,?,?,?)",[
        ("A","abc@abc.com","XYZ","engine leak","2025-1-10"),
        ("A","abc@abc.com","XYZ","engine crack","2025-3-21"),
        ("B","bca@bca.com","ZXY","tyre puncture","2025-7-15")
        ])

    conn.commit()

    cursor.execute("SELECT * FROM users")
    print(cursor.fetchall())
    conn.close()

engine = create_engine("sqlite:///mock_data.db")
db = SQLDatabase(engine)

@tool
def fetch_data(state:data_fetch_schema):
    """
    returns maintanence history from a database based on a key like vehicle model or customer name or Problem,
    example: let these be the data in the database
    ("A","abc@abc.com","XYZ","engine leak","2025-1-10"),
    ("A","abc@abc.com","XYZ","engine crack","2025-3-21"),
    ("B","bca@bca.com","ZXY","tyre puncture","2025-7-15")

    they are in the format (name, email,model,problem,date)

    if the key is name , for example B
    the tool returns ("B","bca@bca.com","ZXY","tyre puncture","2025-7-15")
    """
    print("fetching data")
    query = f"SELECT name, email, problem, date FROM users WHERE model = '{state.model_dump(by_alias=True)['vehicle_model']}'"
    data = db.run(query)
    return data

def fetch_data_RCA_CAPA():
    query = f"SELECT model,problem FROM users"
    data = db.run(query)
    print(data)
    return data

@tool
def log_currnet_data(data:data_base_schema):
    """
    log's or inserts the data into the database given (name,email,model,problem,date), example:- ("A","abc@abc.com","XYZ","engine leak","2025-1-10")
    """
    print("loging data to mock database")
    data = data.model_dump()
    insert_query = f"""
    INSERT INTO users (name,email,model,problem,date)
    VALUES ('{data['name']}', '{data['email']}','{data['model']}','{data['problem']}','{data['Date']}')
    """

    print(db.run(insert_query))
    return f"data of {data["name"]} is loged into the database"