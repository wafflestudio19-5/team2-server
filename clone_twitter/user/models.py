from io import BytesIO

from django.utils.timezone import now
import os
from random import randint
import requests
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from twitter.settings import AWS_S3_CUSTOM_DOMAIN
# Create your models here.

class CustomUserManager(BaseUserManager):

    use_in_migrations = True
    # TODO change to create user with only email / phone-number
    def _create_user(self, user_id, password, **extra_fields):
        # if not email:
        #    raise ValueError('이메일을 설정해주세요.')
        # if email:  # changed
        #    email = self.normalize_email(email)
        img = extra_fields.pop('profile_img', None)  # url(kakao) / file
        url = extra_fields.pop('kakao_profile', None)
        is_social = extra_fields.pop('is_social', False)
        user = self.model(user_id=user_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        profile_media = ProfileMedia(user=user)
        if is_social:
            profile_media.img_url = url
        elif img:
            profile_media.media = img
        profile_media.save()

        return user

    def create_user(self, user_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(user_id, password, **extra_fields)


    def create_superuser(self, password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        email = 'admin@gmail.com'
        if extra_fields.get('is_staff') is not True or extra_fields.get('is_superuser') is not True:
            raise ValueError('권한 설정이 잘못되었습니다.')

        return  self._create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'user_id'

    user_id = models.CharField(max_length=15, unique=True, db_index=True)  # ex) @waffle -> user_id = waffle (up to length 15)
    username = models.CharField(max_length=50)  # nickname ex) Waffle @1234 -> Waffle (up to length 50)
    email = models.EmailField(max_length=100, unique=True, null=True)

    phone_number_pattern = RegexValidator(regex=r"[\d]{3}-[\d]{4}-[\d]{4}")  # another option: 1)validation with drf 2)external library
    phone_number = models.CharField(validators=[phone_number_pattern], max_length=14, unique=True, blank=True, null=True)

    # profile related fields
    # profile_img = models.ImageField(null=True, blank=True, upload_to='profile/')
    header_img = models.ImageField(null=True, blank=True, upload_to='header/')
    bio = models.CharField(max_length=255, blank=True)
    birth_date = models.DateField(null=True)
    # language = models.PositiveSmallIntegerField(choices=LANGUAGE)
    allow_notification = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Q. lanaguage, url field?
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

class Follow(models.Model):
    follower = models.ForeignKey(get_user_model(), related_name='follower', on_delete=models.CASCADE)
    following = models.ForeignKey(get_user_model(), related_name='following', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # no duplicated follow relation
        constraints = [models.UniqueConstraint(fields=['follower', 'following'], name='follower-following relation')]

class SocialAccount(models.Model):
    TYPES = (('kakao', 'Kakao'),)  # add Google later after implementation

    user = models.OneToOneField(get_user_model(), related_name='social_account', on_delete=models.CASCADE)
    type = models.CharField(choices=TYPES, max_length=10)
    account_id = models.IntegerField() # only for kakao login -> unique = true but.. if we add other social login then..

class ProfileMedia(models.Model):
    default_profile_img = 'https://team2-django-media.s3.ap-northeast-2.amazonaws.com/media/profile/default_user_profile.jpeg'

    # def profile_media_directory_path(self, filename):
    #    filename_base, filename_ext = os.path.splitext(filename)
    #    return 'profile/' + self.user.id + '/' + now().strftime('%Y%m%d_%H%M%S') + '_' + str(randint(10000000, 99999999)) + filename_ext

    media = models.FileField(upload_to='profile/')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_img')
    image_url = models.URLField(default=default_profile_img) #only used for social login user / default image