from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    path('<int:number><str:letter>/', views.TimeTableList.as_view(), name="list"),
    path('', views.CurrentTimetableView.as_view(), name="current")
]
