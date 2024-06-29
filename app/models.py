import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import pre_save
from django.dispatch import receiver
import random

def generate_account_number():
    return random.randint(10000000, 99999999)

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The phone number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(unique=True, max_length=15, null=True, blank=False)
    first_name = models.CharField(max_length=30, null=True, blank=False)
    last_name = models.CharField(max_length=30, null=True, blank=False)
    chama = models.ForeignKey('Chama', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_set',
        blank=True,
        help_text='The permissions this user has.',
        verbose_name = 'user permissions',
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.phone_number

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

class Chama(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chama_name = models.CharField(max_length=30, null=True, blank=False)
    chama_account = models.IntegerField(editable=False, unique=True)
    balance = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.chama_account)

class UserAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    acc_id = models.IntegerField(editable=False, unique=True)
    balance = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.acc_id} - {self.user.first_name}"

@receiver(pre_save, sender=UserAccount)
def set_user_account_id(sender, instance, **kwargs):
    if not instance.acc_id:
        instance.acc_id = generate_account_number()

@receiver(pre_save, sender=Chama)
def set_chama_account_id(sender, instance, **kwargs):
    if not instance.chama_account:
        instance.chama_account = generate_account_number()
