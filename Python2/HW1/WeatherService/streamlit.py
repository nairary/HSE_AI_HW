import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import asyncio
import plotly.graph_objects as go
from functools import partial
from manager.time_series_manager.time_series import TSTown, get_season
from manager.temperature_manager.temperature import get_current_temperature_async

def STService():
    st.title("Анализ исторических данных и текущей погоды")
    st.sidebar.header("Загрузка данных")

    # Уникальный ключ для file_uploader
    file = st.sidebar.file_uploader("Загрузите CSV-файл с историческими данными", type="csv", key="unique_file_upload_1")

    if file is not None:
        # Показ сообщения об успешной загрузке
        st.success("Файл успешно загружен!")

        try:
        
            # Чтение файла
            data_original = pd.read_csv(file)

            # Показ первых строк файла
            st.subheader("Просмотр загруженных данных")
            st.dataframe(data_original.head())

            # Проверка наличия столбца 'city'
            if 'city' not in data_original.columns:
                st.error("Файл должен содержать столбец 'city'.")
                return

            # Получение уникальных городов
            cities = data_original['city'].unique()

            # Обработка данных с использованием ThreadPoolExecutor
            task_with_data = partial(TSTown, data_original)
            with ThreadPoolExecutor() as executor:
                results_for_all_cities = list(executor.map(task_with_data, cities))

            # Выбор города
            selected_city = st.sidebar.selectbox("Выберите город", cities)
            idx_city = list(cities).index(selected_city)
            results = results_for_all_cities[idx_city]

            # Настройка API
            st.sidebar.header("Настройки API")
            api_key = st.sidebar.text_input("Введите API-ключ OpenWeatherMap", type="password", key="unique_api_key_1")

            current_temp = None
            if api_key:
                st.header(f"Текущая погода для города {selected_city}")

                # Асинхронный запрос текущей температуры
                current_temp, error = asyncio.run(get_current_temperature_async(selected_city, api_key))

                if current_temp is not None:
                    st.write(f"Текущая температура: {current_temp} °C")
                elif error:
                    st.error(f"Ошибка: {error}")

                # Проверка на аномалии температуры
                season_now = get_season()
                if not results['Профиль сезона'].empty:
                    profile_now = results['Профиль сезона'][results['Профиль сезона']['season'] == season_now]
                    if not profile_now.empty and current_temp is not None:
                        mean_temp = float(profile_now['mean_temperature'].iloc[0])
                        std_temp = float(profile_now['std_temperature'].iloc[0])
                        if abs(current_temp - mean_temp) > 2 * std_temp:
                            st.warning("Температура сейчас аномальна для этого сезона!")
                        else:
                            st.info("Температура в рамках нормы для сезона.")

            # Построение графика
            df = results['Данные']
            anomalies = results['Аномальные точки']

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['temperature'],
                mode='lines',
                name='Температура'
            ))

            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['rolling_mean'],
                mode='lines',
                name='Скользящее среднее'
            ))

            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['trend_line'],
                mode='lines',
                name='Линия тренда'
            ))

            if len(anomalies) > 0:
                fig.add_trace(go.Scatter(
                    x=anomalies['timestamp'],
                    y=anomalies['temperature'],
                    mode='markers',
                    marker=dict(color='red', size=8),
                    name='Аномалии'
                ))

            if current_temp is not None:
                fig.add_hline(
                    y=current_temp,
                    line_dash='dash',
                    annotation_text=f"Текущая {current_temp} °C",
                    annotation_position="top right"
                )

            fig.update_layout(
                title=f"Температура во времени ({selected_city})",
                xaxis_title="Дата",
                yaxis_title="Температура (°C)",
                legend_title="Легенда",
            )

            st.plotly_chart(fig, use_container_width=True)

            # Описательная статистика
            st.subheader("Описательная статистика")
            st.write("Город:", results['Статистика']['Город'])
            st.write("Минимальная температура:", results['Статистика']['Минимальная температура'])
            st.write("Максимальная температура:", results['Статистика']['Максимальная температура'])
            st.write("Средняя температура:", results['Статистика']['Средняя температура'])
            st.write("Наклон тренда:", results['Статистика']['Наклон тренда'])

            # Профиль сезона
            st.subheader("Профиль сезона")
            st.write(results['Профиль сезона'])

        except Exception as e:
            st.error(f"Ошибка при обработке файла: {e}")

    else:
        st.info("Загрузите CSV-файл для анализа.")

if __name__ == '__main__':
    STService()
