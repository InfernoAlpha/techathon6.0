from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def slots_booked():
    data = {
        "name":"A",
        "model":"XYZ",
        "maintenance_status":"maintenance completed"
    }
    return data