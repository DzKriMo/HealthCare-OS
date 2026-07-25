from django.urls import path
from . import views

app_name = "ophthalmology"

urlpatterns = [
    path("exams/", views.ExamListView.as_view(), name="exam-list"),
    path("exams/<uuid:pk>/", views.ExamDetailView.as_view(), name="exam-detail"),
    path("prescriptions/", views.PrescriptionListView.as_view(), name="rx-list"),
]
