from django.urls import path

from app import views

urlpatterns = [
    path('stk-push/', views.StkPushView.as_view(), name='stk-push'),
    path('callback/', views.StkPushCallbackView.as_view(), name='callback'),
    path('login/', views.LoginView.as_view(), name='sign-in'),
    path('logout/', views.LogoutView.as_view(), name='sign-out'),
    path('', views.UserDashboard.as_view(), name='dashboard'),
]