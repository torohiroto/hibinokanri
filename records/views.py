from django.shortcuts import render, redirect, get_object_or_404
from .models import DailyRecord
from .forms import DailyRecordForm
from django.contrib import messages
import json
import requests
from django.http import JsonResponse, HttpResponse
from datetime import datetime, date
import traceback
import csv
# import pandas as pd  <- REMOVED FROM HERE

def index(request):
    return render(request, 'records/index.html')

# ... (other views are the same) ...
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
        weather_params = {"latitude": lat, "longitude": lon, "daily": "weather_code,temperature_2m_max,temperature_2m_min,pressure_msl_max,pressure_msl_min,relative_humidity_2m_mean", "timezone": "Asia/Tokyo", "start_date": target_date_str, "end_date": target_date_str}
        weather_url = "https://api.open-meteo.com/v1/forecast"
        response_weather = requests.get(weather_url, params=weather_params)
        response_weather.raise_for_status()
        weather_data = response_weather.json()
        air_quality_params = {"latitude": lat, "longitude": lon, "hourly": "pm2_5", "start_date": target_date_str, "end_date": target_date_str, "timezone": "Asia/Tokyo"}
        air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        response_air = requests.get(air_quality_url, params=air_quality_params)
        response_air.raise_for_status()
        air_data = response_air.json()
        daily_data = weather_data.get('daily', {})
        weather_code_mapping = {0: 'sunny', 1: 'sunny', 2: 'cloudy', 3: 'cloudy', 45: 'cloudy', 48: 'cloudy', 51: 'rainy', 53: 'rainy', 55: 'rainy', 61: 'rainy', 63: 'rainy', 65: 'rainy', 80: 'rainy', 81: 'rainy', 82: 'rainy'}
        weather_code = daily_data.get('weather_code', [None])[0]
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
        mapped_data = {'weather': weather_code_mapping.get(weather_code, ''), 'max_temperature': daily_data.get('temperature_2m_max', [None])[0], 'min_temperature': daily_data.get('temperature_2m_min', [None])[0], 'max_pressure': daily_data.get('pressure_msl_max', [None])[0], 'min_pressure': daily_data.get('pressure_msl_min', [None])[0], 'humidity': daily_data.get('relative_humidity_2m_mean', [None])[0], 'pm25': pm25_rating}
        return JsonResponse(mapped_data)
    except requests.exceptions.RequestException as e:
        print(f"--- API Request Error: {e}")
        traceback.print_exc()
        return JsonResponse({'error': f'APIの呼び出しに失敗しました: {e}'}, status=500)
    except Exception as e:
        print(f"--- Data Processing Error: {e}")
        traceback.print_exc()
        return JsonResponse({'error': 'サーバーで予期せぬエラーが発生しました。'}, status=500)

def export_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="daily_records.csv"'
    writer = csv.writer(response)
    header = [field.verbose_name for field in DailyRecord._meta.fields]
    writer.writerow(header)
    records = DailyRecord.objects.all().order_by('date')
    for record in records:
        row = [record.id, record.date, record.get_weather_display(), record.max_pressure, record.min_pressure, record.max_temperature, record.min_temperature, record.humidity, record.pollen, record.pm25, record.my_mood, record.wife_mood, record.get_headache_medicine_display(), "有り" if record.mishap else "無し", record.diary]
        writer.writerow(row)
    return response

def ai_analysis(request):
    import pandas as pd # <- MOVED HERE

    records = DailyRecord.objects.all()
    if len(records) < 5:
        return render(request, 'records/ai_analysis.html', {'error': '分析するにはデータが不足しています。少なくとも5日分の記録を入力してください。'})

    df = pd.DataFrame(list(records.values()))
    if df.empty:
        return render(request, 'records/ai_analysis.html', {'error': '分析するデータがありません。'})

    rating_mapping = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    df['my_mood_num'] = df['my_mood'].map(rating_mapping)
    df['wife_mood_num'] = df['wife_mood'].map(rating_mapping)
    df['pollen_num'] = df['pollen'].map(rating_mapping)
    df['pm25_num'] = df['pm25'].map(rating_mapping)

    if 'weather' in df.columns:
        df = pd.get_dummies(df, columns=['weather'], prefix='weather', dummy_na=True)

    df['headache_medicine_num'] = df['headache_medicine'].apply(lambda x: 1 if x == 'yes' else (0 if x == 'no' else None))
    df['mishap_num'] = df['mishap'].astype(int)

    base_cols = ['max_pressure', 'min_pressure', 'max_temperature', 'min_temperature', 'humidity']
    mood_cols = ['my_mood_num', 'wife_mood_num']
    rating_cols = ['pollen_num', 'pm25_num']
    binary_cols = ['headache_medicine_num', 'mishap_num']
    weather_cols = [col for col in df.columns if 'weather_' in col]

    existing_cols = [col for col in (base_cols + mood_cols + rating_cols + binary_cols + weather_cols) if col in df.columns]

    df_corr = df[existing_cols].dropna()

    if len(df_corr) < 2:
        return render(request, 'records/ai_analysis.html', {'error': '分析可能な数値データが不足しています。'})

    corr_matrix = df_corr.corr()

    if 'my_mood_num' not in corr_matrix or 'wife_mood_num' not in corr_matrix:
         return render(request, 'records/ai_analysis.html', {'error': '機嫌のデータが不足しているため、相関を計算できません。'})

    my_mood_corr = corr_matrix['my_mood_num'].sort_values(ascending=False, key=abs).drop('my_mood_num')
    wife_mood_corr = corr_matrix['wife_mood_num'].sort_values(ascending=False, key=abs).drop('wife_mood_num')

    context = {
        'my_mood_corr': my_mood_corr.to_dict(),
        'wife_mood_corr': wife_mood_corr.to_dict(),
    }

    return render(request, 'records/ai_analysis.html', context)
