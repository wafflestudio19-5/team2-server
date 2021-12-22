from django.contrib.auth.models import update_last_login
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
import re
from user.models import Follow

# jwt token setting
User = get_user_model()
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

# [ user -> jwt_token ] function
def jwt_token_of(user):
    payload = JWT_PAYLOAD_HANDLER(user)
    jwt_token = JWT_ENCODE_HANDLER(payload)
    return jwt_token

class UserCreateSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)  # ex) @waffle -> user_id = waffle
    username = serializers.CharField(required=True) # nickname ex) Waffle @1234 -> Waffle
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=False)
    profile_img = serializers.ImageField(required=False)  #TODO set to default image
    header_img = serializers.ImageField(required=False)
    bio = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)
    # language = models.PositiveSmallIntegerField(choices=LANGUAGE)
    allow_notification = serializers.BooleanField(required=False)

    def validate(self, data):
        user_id = data.get('user_id')
        username = data.get('username')
        email = data.get('email')
        phone_number = data.get('phone_number', '')

        if User.objects.filter(user_id=user_id).exists():
            raise serializers.ValidationError("same user_id exsits already")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("same username exsits already")
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("same email exsits already")
        if phone_number == '':  # since '' regarded as duplicate entry in db
            data.update({'phone_number': None})
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("same phonenumber exsits already")
        if phone_number and not self.is_valid_phone_num(phone_number):
            raise serializers.ValidationError("invalid phone number pattern")
        return data

    def is_valid_phone_num(self, phone_number):
        if re.match(r"[\d]{3}-[\d]{4}-[\d]{4}", phone_number):
            return True
        return False

    def create(self, validated_data):
        username = validated_data.get('username')
        email = validated_data.get('email')
        password = validated_data.get('password')
        user_id = validated_data.get('user_id')
        phone_number = validated_data.pop('phone_number', '')
        profile_img = validated_data.get('profile_img')
        header_img = validated_data.get('header_img')
        bio = validated_data.pop('bio', '')
        birth_date = validated_data.get('birth_date')
        allow_notification = validated_data.get('allow_notification')

        user = User.objects.create_user(email=email, user_id=user_id, username=username, password=password,
                                        phone_number=phone_number, profile_img=profile_img, header_img=header_img,
                                        bio=bio, birth_date=birth_date, allow_notification=allow_notification)

        return user, jwt_token_of(user)

class UserLoginSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=20)
    # email = serializers.CharField(max_length=100)
    # phone_number = serializers.CharField(max_length=14)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data): #TODO multi credential... email/user_id/
        user_id = data.get('user_id', None)
        password = data.get('password', None)
        user = authenticate(user_id=user_id, password=password)

        if user is None:
            raise serializers.ValidationError("user id of password is wrong.")

        update_last_login(None, user)
        return {
            'user_id': user.user_id,
            'token': jwt_token_of(user)
        }

class FollowSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=20, required=True)

    def validate(self, data):
        target_user_id = data.get('user_id')
        me = self.context['request'].user
        if not target_user_id:
            raise serializers.ValidationError("specify target user_id.")
        if not User.objects.filter(user_id=target_user_id).exists():
            raise serializers.ValidationError("target user does not exist")
        if me.user_id == target_user_id:
            raise serializers.ValidationError("cannot follow myself")
        return data

    def create(self, validated_data):
        follower = self.context['request'].user
        following = User.objects.get(user_id=validated_data['user_id'])
        follow_relation = Follow.objects.create(follower=follower, following=following)
        return follow_relation

