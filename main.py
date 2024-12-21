import streamlit as st
import requests
import pandas as pd

from analysis import get_all_stats, current_season

url = 'https://api.openweathermap.org/data/2.5/weather'
city = None

st.title('Temperature info')
uploaded_file = st.file_uploader("Загрузите файл с данными в формате csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    city_stats = get_all_stats(df)
    cities = df['city'].unique().tolist()
    city = st.selectbox(
        "Выберите город",
        cities,
        index=None
    )
api_key = st.text_input('OpenWeather Api key')

if city and api_key:
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'
    }
    response = requests.get(url, params=params)
    if response.ok:
        current_city_temp = response.json()['main']['temp']
        st.write(f'Температура в городе {city} = {current_city_temp} C')
        stats = city_stats[city]

        historical_data = stats['city_season_stats'][stats['city_season_stats']['season'] == current_season]
        if (abs(current_city_temp - historical_data['mean']) > 2 * historical_data['std']).item():
            st.write(f'Сейчас в городе аномальная температура! Будьте осторожны')
        else:
            st.write(f'Температура в городе в пределах исторических значений')

        st.write('### Информация о статистиках температуры в городе:')
        global_stats = stats['city_global_stats']
        st.write(f'Минимальная температура за все время = {global_stats["min"]:.2f} °C')
        st.write(f'Максимальная температура за все время = {global_stats["max"]:.2f} °C')
        st.write(f'Средняя температура за все время = {global_stats["mean"]:.2f} °C')

        st.write('Сезонный профиль:')
        st.write(stats['city_season_stats'])

        st.write('Тренд температуры:')
        trend = stats['trend']
        if trend > 0:
            st.write(f'Мы стремительно нагреваемся со скоростью {trend:.6f} градусов в день')
        else:
            st.write(f'Мы стремительно холодеем со скоростью {trend:.6f} градусов в день')

        st.scatter_chart(stats['city_df'], x='timestamp', y='temperature', color='color')
    else:
        st.write('Во время запроса к API произошла ошибка')
        st.write(response.text)
