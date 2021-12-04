from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
# Create your models here.

class CustomUserManager(BaseUserManager):

    use_in_migrations = True
    # TODO change to create user with only email / phone-number
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('이메일을 설정해주세요.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_fields)


    def create_superuser(self, email, password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True or extra_fields.get('is_superuser') is not True:
            raise ValueError('권한 설정이 잘못되었습니다.')

        return  self._create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'user_id'  #TODO

    user_id = models.CharField(max_length=20, unique=True, db_index=True)  # ex) @waffle -> user_id = waffle
    username = models.CharField(max_length=20, unique=True)  # nickname ex) Waffle @1234 -> Waffle
    email = models.EmailField(max_length=100, unique=True)

    phone_number_pattern = RegexValidator(regex=r"[\d]{3}-[\d]{3}-[\d]{3}")  # another option: 1)validation with drf 2)external library
    phone_number = models.CharField(validators=[phone_number_pattern], max_length=14, unique=True, blank=True, null=True)  #TODO null=True

    # profile related fields
    profile_img = models.ImageField(null=True)  # TODO connect to S3. (we store only urls/key in DB)
    header_img = models.ImageField(null=True)
    bio = models.CharField(max_length=255, blank=True)
    birth_date = models.DateField(null=True)
    # language = models.PositiveSmallIntegerField(choices=LANGUAGE)
    allow_notification = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Q. lanaguage, url field?

    objects = CustomUserManager()

    def clean_phone_number(self):
        if self.phone_number == "":
            self.phone_number = None