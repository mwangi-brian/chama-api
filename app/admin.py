from django.contrib import admin
from .models import User, Transaction, Chama

admin.site.register(User)
admin.site.register(Chama)
admin.site.register(Transaction)