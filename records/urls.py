from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.record_list, name='record_list'),
    path('new/', views.create_record, name='create_record'),
    path('<int:pk>/edit/', views.update_record, name='update_record'),
    path('<int:pk>/delete/', views.delete_record, name='delete_record'),
    path('visualize/', views.data_visualization, name='data_visualization'),
    path('api/get-weather/', views.get_weather_data, name='get_weather_data'),
    path('export/csv/', views.export_csv, name='export_csv'),
]
