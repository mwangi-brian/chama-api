from django.contrib import admin
from .models import User, UserAccount, Chama

admin.site.register(UserAccount)
admin.site.register(User)
admin.site.register(Chama)