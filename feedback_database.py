import sqlite3
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from schema import data_log_feedback,data_fetch_feedback

if __name__ == "__main__":
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY,
        name TEXT,
        model TEXT,
        rating DECIMAL(3, 2),
        feedback TEXT,
        date DATE,
        garage TEXT
    )
    """)

    cursor.executemany("INSERT INTO feedback (name,model,rating,feedback,date,garage) VALUES (?,?,?,?,?,?)",[
        ("A","XYZ",3,"bad expirence with mechanics","2025-1-10","A motors"),
        ("B","XYZ",4,"too expensive","2025-3-21","A motors"),
        ("C","ZXY",3,"short staffed","2025-7-15","B motors")
        ])

    conn.commit()

    cursor.execute("SELECT * FROM feedback")
    print(cursor.fetchall())
    conn.close()

engine = create_engine("sqlite:///feedback.db")
db = SQLDatabase(engine)

@tool
def fetch_feedback(state:data_fetch_feedback):
    """
    returns feedback history from a database based on a key like vehicle model or customer name,
    example: let these be the data in the database
    ("A","XYZ",3,"bad expirence with mechanics","2025-1-10","A motors"),
    ("B","XYZ",4,"too expensive","2025-3-21","A motors"),
    ("C","ZXY",3,"short staffed","2025-7-15","B motors")

    they are in the format (name,model,rating,feedback,date,garage)

    if the key is rating , for example A
    the tool returns ("A","XYZ",3,"bad expirence with mechanics","2025-1-10","A motors")
    """
    print("fetching data")
    query = f"SELECT name,model,rating,feedback,date,garage FROM feedback WHERE {state.model_dump(by_alias=True)['key']} = '{state.model_dump(by_alias=True)['key_value']}'"
    data = db.run(query)
    return data

@tool
def log_feedback(data:data_log_feedback):
    """
    log's or inserts the data into the feedback database
    """
    print("loging data")
    data = data.model_dump()
    insert_query = f"""
    INSERT INTO feedback (name,model,rating,feedback,date,garage)
    VALUES ('{data['name']}','{data['model']}','{data['rating']}','{data['feedback']}','{data['Date']}','{data['garage']}')
    """

    db.run(insert_query)
    return data