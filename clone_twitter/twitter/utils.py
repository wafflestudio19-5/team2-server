import os
from random import randint
import uuid
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.utils.timezone import now



def random_string_generator():
    random = str(uuid.uuid4())
    random = random.upper()
    return random[0:6]


def unique_random_id_generator(manager):
    new_id = random_string_generator()

    if manager.objects.filter(user_id=new_id):
        return unique_random_id_generator()
    return new_id

def unique_random_email_generator(manager):
    new_email = random_string_generator().join('@fakeemail.com')

    if manager.objects.filter(email=new_email):
        return unique_random_email_generator()
    return new_email

def media_directory_path(instance, filename, usage='tweet'):
    filename_base, filename_ext = os.path.splitext(filename)
    return usage+'/'+now().strftime('%Y%m%d_%H%M%S')+'_'+str(randint(10000000,99999999))+filename_ext


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (six.text_type(user.pk) + six.text_type(timestamp)) +  six.text_type(user.is_active)

account_activation_token = AccountActivationTokenGenerator()

def active_message(domain, uidb64, token):
    return f"아래 링크를 클릭하면 회원가입 인증이 완료됩니다.\n\n 회원가입링크 : http://{domain}/user/account/activate/{uidb64}/{token}\n\n감사합니다."
