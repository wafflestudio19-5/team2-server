import os
from random import randint
import uuid

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

