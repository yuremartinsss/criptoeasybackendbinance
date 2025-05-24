
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pandas_ta as ta
import requests
from dotenv import load_dotenv
import os
import numpy as np


load_dotenv()

app = FastAPI()

# CORS liberado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY")


class AnaliseRequest(BaseModel):
    symbol: str
    interval: str


@app.get("/")
def read_root():
    return {"message": "API Criptoeasy rodando 100%, Binance conectada!"}


@app.post("/analisar")
def analisar_dados(request: AnaliseRequest):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={request.symbol}&interval={request.interval}&limit=100"
        headers = {
            "X-MBX-APIKEY": API_KEY,
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": f"Erro ao buscar dados da Binance. Status code: {response.status_code}"}

        data = response.json()

        df = pd.DataFrame(data, columns=[
            "Open time", "Open", "High", "Low", "Close", "Volume",
            "Close time", "Quote asset volume", "Number of trades",
            "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
        ])

        df["Close"] = df["Close"].astype(float)

        df["RSI"] = ta.rsi(df["Close"])
        df["EMA20"] = ta.ema(df["Close"], length=20)
        df["EMA50"] = ta.ema(df["Close"], length=50)

        rsi = round(df["RSI"].iloc[-1], 2) if not pd.isna(df["RSI"].iloc[-1]) else "Indisponível"
        ema20 = round(df["EMA20"].iloc[-1], 2) if not pd.isna(df["EMA20"].iloc[-1]) else "Indisponível"
        ema50 = round(df["EMA50"].iloc[-1], 2) if not pd.isna(df["EMA50"].iloc[-1]) else "Indisponível"
        preco_atual = df["Close"].iloc[-1]

        if ema20 > ema50:
            tendencia = "Tendência de Alta"
        elif ema20 < ema50:
            tendencia = "Tendência de Baixa"
        else:
            tendencia = "Indefinida"

        return {
            "Tendência": tendencia,
            "Preço Atual": preco_atual,
            "RSI": rsi,
            "EMA20": ema20,
            "EMA50": ema50
        }
    except Exception as e:
        return {"error": str(e)}
