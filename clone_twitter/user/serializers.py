from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

# jwt token setting
User = get_user_model()
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

# [ user -> jwt_token ] function
def jwt_token_of(user):
    payload = JWT_PAYLOAD_HANDLER(user)
    jwt_token = JWT_ENCODE_HANDLER(payload)
    return jwt_token

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'user_id',
            'username',
            'email',
            'phone_number',
            'profile_img',
            'header_img',
            'bio',
            'birth_date',
            # language
            # allow_notification
            'created_at',
        )

    def validate(self, data):
        user_id = data.get('user_id')
        username = data.get('username')
        email = data.get('email')
        phone_number = data.get('phone_number')

        if User.objects.filter(user_id=user_id).exists():
            raise serializers.ValidationError("same user_id exsits already")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("same username exsits already")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("same email exsits already")
        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("same phonenumber exsits already")
        return data