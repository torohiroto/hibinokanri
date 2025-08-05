from django.shortcuts import render, redirect, get_object_or_404
from .models import DailyRecord
from .forms import DailyRecordForm
from django.contrib import messages
import json

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
