# -*- coding: utf-8 -*-
"""Actividad 7 - Continuación de Pruebas de raíz unitaria

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mrpM0JD8nr9cmdOsRDnqxgXRRfBJBs07
"""

# Librerías necesarias
import pandas as pd
import numpy as np
from google.colab import files
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import matplotlib.pyplot as plt
from itertools import combinations

plt.style.use('seaborn-v0_8-whitegrid')

# Nombres simbólicos de las acciones
tickers = ['AAPL', 'CAT', 'SPOT', 'MCD']
data = {}

# Subir archivos y leer automáticamente
for ticker in tickers:
    print(f"🔼 Sube el archivo de precios para: {ticker} (solo 1 columna sin encabezado 'Date')")
    uploaded = files.upload()
    filename = list(uploaded.keys())[0]
    df = pd.read_excel(filename)

    if df.shape[1] != 1:
        raise ValueError(f"⚠️ El archivo para {ticker} debe tener solo UNA columna con precios.")

    data[ticker] = df.iloc[:, 0]

# Alinear longitud de las series
min_len = min(len(series) for series in data.values())
for t in tickers:
    data[t] = data[t].iloc[:min_len].reset_index(drop=True)

# Correlogramas y tests de estacionariedad
def correlogram_tests(series, name):
    print(f"\n📊 Correlogramas para {name}")
    plt.figure(figsize=(14,4))
    plt.subplot(1,2,1)
    plot_acf(series, ax=plt.gca(), lags=36)
    plt.title(f"{name} - ACF")
    plt.subplot(1,2,2)
    plot_pacf(series, ax=plt.gca(), lags=36, method='ywm')
    plt.title(f"{name} - PACF")
    plt.tight_layout()
    plt.show()

    print(f"\n🔍 Prueba ADF para {name}")
    adf = adfuller(series)
    print(f"ADF Statistic: {adf[0]:.4f} | p-value: {adf[1]:.4f}")
    print(f"Critical Values: {adf[4]}")
    print("→ Estacionaria" if adf[1] < 0.05 else "→ No estacionaria")

    print(f"\n🔍 Prueba KPSS para {name}")
    kpss_result = kpss(series, nlags="auto")
    print(f"KPSS Statistic: {kpss_result[0]:.4f} | p-value: {kpss_result[1]:.4f}")
    print(f"Critical Values: {kpss_result[3]}")
    print("→ Estacionaria" if kpss_result[1] >= 0.05 else "→ No estacionaria")

    if adf[1] >= 0.05 and kpss_result[1] < 0.05:
        print(f"\n🌀 {name} parece seguir una caminata aleatoria.")
    else:
        print(f"\n✔️ {name} no parece una caminata aleatoria.")

# Aplicar análisis a cada serie
for ticker in tickers:
    correlogram_tests(data[ticker], ticker)

# Test de cointegración Johansen entre pares
print("\n💥 Test de Cointegración de Johansen para pares:")
for pair in combinations(tickers, 2):
    df_pair = pd.DataFrame({pair[0]: data[pair[0]], pair[1]: data[pair[1]]})
    print(f"\n{pair[0]} vs {pair[1]}")
    result = coint_johansen(df_pair, det_order=0, k_ar_diff=1)
    print(f"Trace Stats: {result.lr1}")
    print(f"Critical values (95%): {result.cvt[:,1]}")
    if result.lr1[0] > result.cvt[0,1]:
        print("✅ Cointegración detectada")
    else:
        print("❌ No hay cointegración significativa")

# ARIMA + Pronóstico
def best_arima(series, name, steps=30):
    print(f"\n📈 Buscando mejor ARIMA para {name}")
    best_aic = float('inf')
    best_order = None
    for p in range(4):
        for d in range(3):
            for q in range(4):
                try:
                    model = ARIMA(series, order=(p,d,q)).fit()
                    if model.aic < best_aic:
                        best_aic = model.aic
                        best_order = (p,d,q)
                except:
                    continue
    print(f"🏆 Mejor ARIMA({best_order}) con AIC={best_aic:.2f}")

    final_model = ARIMA(series, order=best_order).fit()
    forecast = final_model.get_forecast(steps=steps)
    pred = forecast.predicted_mean
    ci = forecast.conf_int()

    forecast_index = range(len(series), len(series) + steps)

    plt.figure(figsize=(12,6))
    plt.plot(series, label=f"{name} histórico")
    plt.plot(forecast_index, pred, label='Pronóstico', color='red')
    plt.fill_between(forecast_index, ci.iloc[:,0], ci.iloc[:,1], alpha=0.3, color='pink')
    plt.title(f"{name} - Pronóstico 30 días")
    plt.legend()
    plt.show()

    last = series.iloc[-1]
    print(f"Último valor observado: {last:.2f}")
    print(f"Media del pronóstico: {pred.mean():.2f}")
    if pred.mean() > last:
        print("Tendencia esperada: ⬆️ Al alza")
    elif pred.mean() < last:
        print("Tendencia esperada: ⬇️ A la baja")
    else:
        print("Tendencia esperada: ➡️ Estable")
    print(f"Intervalo al final: [{ci.iloc[-1,0]:.2f}, {ci.iloc[-1,1]:.2f}]")
    print(f"Primeros 5 valores:\n{pred[:5]}")

# Ejecutar ARIMA y forecast
for ticker in tickers:
    best_arima(data[ticker], ticker)