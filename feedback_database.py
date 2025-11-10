import sqlite3
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from schema import data_base_schema,data_fetch_schema

if __name__ == "__main__":
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY,
        name TEXT,
        model TEXT,
        feedback TEXT,
        date DATE,
        garage TEXT
    )
    """)

    cursor.executemany("INSERT INTO feedback (name,model,feedback,date,garage) VALUES (?,?,?,?,?)",[
        ("A","XYZ","bad expirence with mechanics","2025-1-10","A motors"),
        ("B","XYZ","too expensive","2025-3-21","A motors"),
        ("C","ZXY","short staffed","2025-7-15","B_motors")
        ])

    conn.commit()

    cursor.execute("SELECT * FROM feedback")
    print(cursor.fetchall())
    conn.close()

engine = create_engine("sqlite:///mock_data.db")
db = SQLDatabase(engine)

@tool
def fetch_data(state:data_fetch_schema):
    """
    returns maintanence history from a database based on a key like vehicle model or customer name,
    example: let these be the data in the database
    ("A","abc@abc.com","XYZ","engine leak","2025-1-10"),
    ("A","abc@abc.com","XYZ","engine crack","2025-3-21"),
    ("B","bca@bca.com","ZXY","tyre puncture","2025-7-15")

    they are in the format (name, email,model,problem,date)

    if the key is name , for example A
    the tool returns ("B","bca@bca.com","ZXY","tyre puncture","2025-7-15")
    """
    print("fetching data")
    query = f"SELECT name, email, problem, date FROM feedback WHERE model = '{state.model_dump(by_alias=True)['vehicle_model']}'"
    data = db.run(query)
    return data

@tool
def log_currnet_data(data:data_base_schema):
    """
    log's or inserts the data into the database
    """
    print("loging data")
    insert_query = f"""
    INSERT INTO feedback (name, email,model,problem,date)
    VALUES ('{data['name']}', '{data['email']}','{data['model']}','{data['problem']}','{data['date']}')
    """

    db.run(insert_query)