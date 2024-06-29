from django.urls import path

from app import views

urlpatterns = [
    path('stk-push/', views.StkPushView, name='stk-push'),
    path('callback/', views.StkPushCallbackView, name='callback'),
    path('login/', views.LoginView, name='sign-in'),
    path('logout/', views.LogoutView.as_view(), name='sign-out'),
]