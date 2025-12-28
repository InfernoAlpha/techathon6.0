from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def dummy_data():
    data = {
        "ID":1,
        "customer_name":"Charith",
        "model":"XYZ",
        "date":"2025-12-17",
        "Email":"Charith@gmail.com",
        "Engine_rpm":876,
        "lub_oil_pressure":2.941605932,
        "Fuel_pressure":16.19386556,
        "Coolant_pressure":2.464503704,
        "lub_oil_temp":77.64093415,
        "Coolent_temp":82.4457245,
    }
    return data