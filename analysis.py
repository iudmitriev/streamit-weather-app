import pandas as pd
from sklearn.linear_model import LinearRegression

from datetime import datetime
from multiprocessing import Pool
from itertools import repeat

month_to_season = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn"
}
current_season = month_to_season[datetime.now().month]

def get_season_stats(city_df: pd.DataFrame):
    rolling_city_mean = city_df[['timestamp', 'temperature']].rolling(
        window=30, on='timestamp', min_periods=1
    ).mean()
    rolling_city_mean = rolling_city_mean.reset_index()
    rolling_city_mean['season'] = pd.to_datetime(
        rolling_city_mean['timestamp']
    ).dt.month.apply(lambda month: month_to_season[month])
    city_season_stats = rolling_city_mean.groupby(by=['season'])['temperature'].agg(
        ['mean', 'std']
    ).reset_index()
    return city_season_stats

def get_anomalies(city_df: pd.DataFrame, city_season_stats: pd.DataFrame):
    city_df = city_df.merge(city_season_stats, on=['season'], how='left')
    city_df['anomaly'] = (city_df['temperature'] - city_df['mean']).abs() > 2 * city_df['std']
    city_df['color'] = city_df['anomaly'].apply(lambda is_anomaly: '#ff0000' if is_anomaly else '#00ff00')
    return city_df

def get_global_stats(city_df: pd.DataFrame):
    return {
        'min': city_df['temperature'].min(),
        'mean': city_df['temperature'].mean(),
        'max': city_df['temperature'].max(),
    }

def get_trend(city_df: pd.DataFrame):    
    model = LinearRegression()
    timestamp = pd.to_datetime(city_df['timestamp'])
    X = pd.DataFrame((timestamp - timestamp.min()).dt.days)
    y = city_df['temperature']
    model.fit(X, y)
    return model.coef_[0]

def get_city_stats(df: pd.DataFrame, city: str):
    city_df = df[df['city'] == city]
    city_season_stats = get_season_stats(city_df=city_df)
    city_df = get_anomalies(city_df=city_df, city_season_stats=city_season_stats)
    city_global_stats = get_global_stats(city_df=city_df)
    trend = get_trend(city_df=city_df)

    return {
        'city_df': city_df, 
        'city_season_stats': city_season_stats,
        'city_global_stats': city_global_stats,
        'trend': trend
    }


def get_all_stats(df: pd.DataFrame):
    cities = df['city'].unique().tolist()
    with Pool(processes=8) as p:
        all_stats = p.starmap(get_city_stats, zip(repeat(df), cities))
    
    city_info = {}
    for i, city in enumerate(cities):
        city_info[city] = all_stats[i]
    return city_info
