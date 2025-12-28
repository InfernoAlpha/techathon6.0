from xgboost import XGBClassifier
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np
from langchain.tools import tool
from schema import model_schema
import logging

if __name__ == "__main__":
    
    data = pd.read_csv("engine_data.csv")
    X = data.drop("Engine Condition",axis=1)
    Y = data["Engine Condition"]

    X_train,X_test,Y_train,Y_test = train_test_split(X,Y,test_size=0.2,random_state=3)

    model = XGBClassifier(objective="binary:logistic",
        eval_metric="logloss",
        learning_rate=0.1,
        max_depth=5,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8
    )

    model.fit(X_train,Y_train,verbose=True)

    Y_pred = model.predict(X_test)
    print("Accuracy:",accuracy_score(Y_test,Y_pred))
    model.save_model("model.json")
    model.load_model("model.json")
    #data = pd.DataFrame([[619,5.672918584,15.73887141,2.052251454,78.39698883,87.00022538]],columns=['Engine rpm', 'Lub oil pressure', 'Fuel pressure', 'Coolant pressure', 'lub oil temp', 'Coolant temp'])
    #data = xgb.DMatrix(data)
    #pred = model.predict(data)
    #print(f"prediction: {pred}")

    #print(model_inference({'data': {'Engine rpm': 876, 'Lub oil pressure': 2.941605932, 'Fuel pressure': 16.19386556, 'Coolant pressure': 2.464503704, 'lub oil temp': 77.64093415, 'Coolant temp': 82.4457245}}))

@tool
def model_inference(data:model_schema) -> dict:
    """
    tool used to asses the vehicle condition based on the parameters given
    """
    model = XGBClassifier(objective="binary:logistic",
        eval_metric="logloss",
        learning_rate=0.1,
        max_depth=5,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8
    )
    model.load_model("model.json")
    print("inferencing model")
    dataframe = pd.DataFrame([data.model_dump(by_alias=True)])
    result = "no engine failure" if model.predict(dataframe) else "engine failure"
    return result