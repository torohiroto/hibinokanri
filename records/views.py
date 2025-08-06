from django.shortcuts import render, redirect, get_object_or_404
from .models import DailyRecord
from .forms import DailyRecordForm
from django.contrib import messages
import json
import os
import requests
from django.http import JsonResponse
from datetime import datetime, date, timedelta

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
            # Add an error message if the date already exists
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
    # Use the same form template for editing
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

    context = {
        'chart_data': json.dumps(chart_data)
    }

    return render(request, 'records/visualization.html', context)

def get_weather_data(request):
    target_date_str = request.GET.get('date')
    if not target_date_str:
        return JsonResponse({'error': '日付が指定されていません。'}, status=400)

    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '無効な日付形式です。YYYY-MM-DD形式で指定してください。'}, status=400)

    # Coordinates for Imabari, Ehime, Japan
    lat = 34.0663
    lon = 132.9949

    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return JsonResponse({'error': 'APIキーが設定されていません。'}, status=500)

    # Decide whether to use historical or forecast API
    today = date.today()
    if target_date < today:
        # Historical data request
        # Note: OneCall 3.0 historical is not free for more than a few days back.
        # This implementation assumes we are fetching recent past data.
        dt = int(datetime.combine(target_date, datetime.min.time()).timestamp())
        url = f"http://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={dt}&appid={api_key}&units=metric&lang=ja"
    else:
        # Forecast data request
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,current&appid={api_key}&units=metric&lang=ja"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Find the correct data for the target date
        weather_data = None
        if 'daily' in data: # Forecast response
            for day_data in data['daily']:
                if date.fromtimestamp(day_data['dt']) == target_date:
                    weather_data = day_data
                    break
        elif 'data' in data: # Historical response
            weather_data = data['data'][0] # It returns data for the requested timestamp

        if not weather_data:
            return JsonResponse({'error': '指定された日付のデータが見つかりませんでした。'}, status=404)

        # Map API response to our model fields
        weather_mapping = {
            'Clear': 'sunny', 'Clouds': 'cloudy', 'Rain': 'rainy',
            'Drizzle': 'rainy', 'Thunderstorm': 'rainy', 'Snow': 'rainy',
            'Mist': 'cloudy', 'Haze': 'cloudy', 'Fog': 'cloudy',
        }

        # The historical response has a different structure for temp
        if 'temp' in weather_data and isinstance(weather_data['temp'], dict):
            max_temp = weather_data['temp']['max']
            min_temp = weather_data['temp']['min']
        else:
            max_temp = weather_data.get('temp')
            min_temp = weather_data.get('temp')


        mapped_data = {
            'weather': weather_mapping.get(weather_data['weather'][0]['main'], ''),
            'max_temperature': max_temp,
            'min_temperature': min_temp,
            'humidity': weather_data['humidity'],
            'pressure': weather_data['pressure'],
        }

        # TODO: Add separate call for Air Pollution API to get PM2.5

        return JsonResponse(mapped_data)

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'APIの呼び出しに失敗しました: {e}'}, status=500)
