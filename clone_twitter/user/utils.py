import uuid
import string
from user.models import User


def random_string_generator():
    random = str(uuid.uuid4())
    random = random.upper()
    return random[0:6]


def unique_random_id_generator():
    new_id = random_string_generator()

    if User.objects.filter(user_id=new_id):
        return unique_random_id_generator()
    return new_id
