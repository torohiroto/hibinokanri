from django.shortcuts import render, redirect, get_object_or_404
from .models import DailyRecord
from .forms import DailyRecordForm
from django.contrib import messages
import json
import requests
from django.http import JsonResponse
from datetime import datetime, date
import traceback

def index(request):
    return render(request, 'records/index.html')

def record_list(request):
    records = DailyRecord.objects.all()
    return render(request, 'records/record_list.html', {'records': records})

def create_record(request):
    if request.method == 'POST':
        form = DailyRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '記録が正常に作成されました。')
            return redirect('record_list')
        else:
            if 'date' in form.errors:
                messages.error(request, 'この日付の記録は既に存在します。編集してください。')
    else:
        form = DailyRecordForm()
    return render(request, 'records/record_form.html', {'form': form})

def update_record(request, pk):
    record = get_object_or_404(DailyRecord, pk=pk)
    if request.method == 'POST':
        form = DailyRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, '記録が正常に更新されました。')
            return redirect('record_list')
    else:
        form = DailyRecordForm(instance=record)
    return render(request, 'records/record_form.html', {'form': form})

def delete_record(request, pk):
    record = get_object_or_404(DailyRecord, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, '記録が正常に削除されました。')
        return redirect('record_list')
    return render(request, 'records/record_confirm_delete.html', {'record': record})

def data_visualization(request):
    records = DailyRecord.objects.all().order_by('date')
    dates = [record.date.strftime('%Y-%m-%d') for record in records]
    rating_mapping = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    chart_data = {
        'dates': dates,
        'datasets': {
            'my_mood': [rating_mapping.get(r.my_mood) for r in records],
            'wife_mood': [rating_mapping.get(r.wife_mood) for r in records],
            'max_temp': [r.max_temperature for r in records],
            'min_temp': [r.min_temperature for r in records],
            'max_pressure': [r.max_pressure for r in records],
            'min_pressure': [r.min_pressure for r in records],
            'humidity': [r.humidity for r in records],
            'pollen': [rating_mapping.get(r.pollen) for r in records],
            'pm25': [rating_mapping.get(r.pm25) for r in records],
        }
    }
    context = {'chart_data': json.dumps(chart_data)}
    return render(request, 'records/visualization.html', context)

def get_weather_data(request):
    target_date_str = request.GET.get('date')
    if not target_date_str:
        return JsonResponse({'error': '日付が指定されていません。'}, status=400)

    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '無効な日付形式です。YYYY-MM-DD形式で指定してください。'}, status=400)

    lat = 34.0663
    lon = 132.9949

    try:
        # --- Get main weather data ---
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,surface_pressure_mean,relative_humidity_2m_mean",
            "timezone": "Asia/Tokyo",
            "start_date": target_date_str,
            "end_date": target_date_str,
        }
        weather_url = "https://api.open-meteo.com/v1/forecast"
        response_weather = requests.get(weather_url, params=weather_params)
        response_weather.raise_for_status()
        weather_data = response_weather.json()

        # --- Get air quality data ---
        air_quality_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "pm2_5",
            "start_date": target_date_str,
            "end_date": target_date_str,
            "timezone": "Asia/Tokyo",
        }
        air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        response_air = requests.get(air_quality_url, params=air_quality_params)
        response_air.raise_for_status()
        air_data = response_air.json()

        # --- Process and combine data ---
        daily_data = weather_data.get('daily', {})

        # WMO Weather code mapping
        weather_code_mapping = {
            0: 'sunny',  # Clear sky
            1: 'sunny',  # Mainly clear
            2: 'cloudy', # Partly cloudy
            3: 'cloudy', # Overcast
            45: 'cloudy',# Fog
            48: 'cloudy',# Depositing rime fog
            51: 'rainy', 53: 'rainy', 55: 'rainy', # Drizzle
            61: 'rainy', 63: 'rainy', 65: 'rainy', # Rain
            80: 'rainy', 81: 'rainy', 82: 'rainy', # Rain showers
        }
        weather_code = daily_data.get('weather_code', [None])[0]

        # PM2.5 rating
        pm25_avg = None
        if air_data.get('hourly', {}).get('pm2_5'):
            pm25_values = [v for v in air_data['hourly']['pm2_5'] if v is not None]
            if pm25_values:
                pm25_avg = sum(pm25_values) / len(pm25_values)

        pm25_rating = ''
        if pm25_avg is not None:
            if pm25_avg <= 12: pm25_rating = 'S'
            elif pm25_avg <= 35: pm25_rating = 'A'
            elif pm25_avg <= 55: pm25_rating = 'B'
            elif pm25_avg <= 150: pm25_rating = 'C'
            else: pm25_rating = 'D'

        mapped_data = {
            'weather': weather_code_mapping.get(weather_code, ''),
            'max_temperature': daily_data.get('temperature_2m_max', [None])[0],
            'min_temperature': daily_data.get('temperature_2m_min', [None])[0],
            'humidity': daily_data.get('relative_humidity_2m_mean', [None])[0],
            'pressure': daily_data.get('surface_pressure_mean', [None])[0],
            'pm25': pm25_rating,
        }

        return JsonResponse(mapped_data)

    except requests.exceptions.RequestException as e:
        print(f"--- API Request Error: {e}")
        traceback.print_exc()
        return JsonResponse({'error': f'APIの呼び出しに失敗しました: {e}'}, status=500)
    except Exception as e:
        print(f"--- Data Processing Error: {e}")
        traceback.print_exc()
        return JsonResponse({'error': 'サーバーで予期せぬエラーが発生しました。'}, status=500)
