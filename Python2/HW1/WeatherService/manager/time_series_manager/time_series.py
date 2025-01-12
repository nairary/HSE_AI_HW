
import pandas as pd
import numpy as np
from datetime import date
from multiprocessing import Pool

def TSTown(data_original: pd.DataFrame, town: str):
    data = data_original[data_original['city'] == town].copy()
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.sort_values(by='timestamp')

    rolling_window = 30
    data['rolling_mean'] = data['temperature'].rolling(window=rolling_window).mean()
    data['rolling_std'] = data['temperature'].rolling(window=rolling_window).std()

    data['Is_Anomaly'] = abs(data['temperature'] - data['rolling_mean']) > 2 * data['rolling_std']
    anomalies = data.loc[data['Is_Anomaly']].reset_index(drop=True)

    season_profile = data.groupby('season').agg(
        mean_temperature=('temperature', 'mean'),
        std_temperature=('temperature', 'std'),
        mean_rolling_temperature=('rolling_mean', 'mean'),
        std_rolling_temperature=('rolling_mean', 'std')
    ).reset_index()

    x = (data['timestamp'] - data['timestamp'].min()).dt.days.astype(float)
    y = data['temperature'].astype(float)
    coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
    slope, intercept = coeffs[0], coeffs[1]

    data['trend_line'] = np.polyval(coeffs, x)

    statistics = {
        'Город': town,
        'Минимальная температура': data['temperature'].min(),
        'Максимальная температура': data['temperature'].max(),
        'Средняя температура': data['temperature'].mean(),
        'Наклон тренда': slope
    }

    return {
        'Статистика': statistics, 
        'Профиль сезона': season_profile, 
        'Аномальные точки': anomalies,
        'Данные': data.reset_index(drop=True),
        'TrendCoeffs': (slope, intercept)
    }

def get_season():
    current_date = date.today()
    month = current_date.month
    day = current_date.day
    if (month == 12) or (1 <= month <= 2):
        return 'winter'
    elif (3 <= month <= 5):
        return 'spring'
    elif (6 <= month <= 8):
        return 'summer'
    else:
        return 'autumn'