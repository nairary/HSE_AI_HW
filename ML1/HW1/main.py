
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import FastAPI, File, UploadFile
from typing import List
import pandas as pd
import joblib
import re

app = FastAPI()
required_fields = ['year', 'km_driven', 'mileage', 'engine', 'max_power', 'seats']
scaler = joblib.load('scaler.joblib')
model = joblib.load('GSCV_model.joblib')

def extract_numeric(value):
    if isinstance(value, str):
        return float(re.search(r"[\d.]+", value).group())
    return float(value)

def preprocess_input(data: dict) -> List[float]:
    fields = required_fields
    return [extract_numeric(data.get(field)) for field in fields]

class Item(BaseModel):
    name: str
    year: int
    km_driven: int
    fuel: str
    seller_type: str
    transmission: str
    owner: str
    mileage: str
    engine: str
    max_power: str
    torque: str
    seats: float

class Items(BaseModel):
    objects: List[Item]

@app.post("/predict_item")
def predict_item(item: Item) -> float:
    features = preprocess_input(item.dict())
    prediction = model.predict(scaler.transform([features]))[0]
    return prediction

@app.post("/predict_items")
async def predict_items_csv(file: UploadFile = File(...)) -> FileResponse:
    data = pd.read_csv(file.file)
    for field in required_fields:
        data[field] = data[field].apply(extract_numeric)
    predictions = model.predict(scaler.transform(data[required_fields]))
    data["selling_price"] = predictions
    output_file = "predicted_items.csv"
    data.to_csv(output_file, index=False)
    return FileResponse(output_file, media_type="text/csv", filename="predicted_items.csv")
