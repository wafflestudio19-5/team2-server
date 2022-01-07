from django.contrib.auth.models import update_last_login
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
import re
from tweet.serializers import TweetSerializer
from user.models import Follow
from django.db.models import Q

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
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    profile_img = serializers.ImageField(required=False)  #TODO set to default image
    header_img = serializers.ImageField(required=False)
    bio = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)
    # language = models.PositiveSmallIntegerField(choices=LANGUAGE)
    allow_notification = serializers.BooleanField(required=False, default=True)

    def validate(self, data):
        user_id = data.get('user_id')
        email = data.get('email', '')
        phone_number = data.get('phone_number', '')

        if User.objects.filter(user_id=user_id).exists():
            raise serializers.ValidationError("same user_id exists already")

        if phone_number == '':  # since '' regarded as duplicate entry in db
            data.update({'phone_number': None})
        if email == '':  # since '' regarded as duplicate entry in db
            data.update({'email': None})

        if not email and not phone_number:
            raise serializers.ValidationError("at least email or phone_number is required")
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("same email exists already")
        if phone_number:
            if User.objects.filter(phone_number=phone_number).exists():
                raise serializers.ValidationError("same phonenumber exsits already")
            if not self.is_valid_phone_num(phone_number):
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
        phone_number = validated_data.pop('phone_number', None)
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

class UserFollowSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='follower.id')
    username = serializers.CharField(source='follower.username')
    user_id = serializers.CharField(source='follower.user_id')
    bio = serializers.CharField(source='follower.bio')
    profile_img = serializers.ImageField(source='follower.profile_img')
    follows_me = serializers.SerializerMethodField()
    i_follow = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id',
            'username',
            'user_id',
            'bio',
            'follows_me',
            'profile_img',
            'i_follow',
        )

    def get_follows_me(self, follow):
        me = self.context['request'].user
        follows_me = Follow.objects.filter(Q(follower=follow.follower) & Q(following=me)).exists()
        return follows_me

    def get_i_follow(self, follow):
        me = self.context['request'].user
        user = follow.follower
        i_follow = user.following.filter(follower=me).count()
        return i_follow == 1


class UserFollowingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='following.id')
    username = serializers.CharField(source='following.username')
    user_id = serializers.CharField(source='following.user_id')
    bio = serializers.CharField(source='following.bio')
    profile_img = serializers.ImageField(source='following.profile_img')
    follows_me = serializers.SerializerMethodField()
    i_follow = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id',
            'username',
            'user_id',
            'bio',
            'follows_me',
            'profile_img',
            'i_follow'
        )

    def get_follows_me(self, follow):
        me = self.context['request'].user
        follows_me = Follow.objects.filter(Q(follower=follow.following) & Q(following=me)).exists()
        return follows_me

    def get_i_follow(self, follow):
        me = self.context['request'].user
        user = follow.following
        i_follow = user.following.filter(follower=me).count()
        return i_follow == 1


class UserRecommendSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'user_id',
            'profile_img',
            'bio',
            # Q. id ?
        ]

          
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    # TODO add image field after setting image server
    # profile_img = serializers.ImageField(allow_null=True, allow_blank=True)
    # header_img = serializers.ImageField(allow_null=True, allow_blank=True)
    bio = serializers.CharField(allow_blank=True)
    birth_date =serializers.DateField(allow_null=True)

    class Meta:
        model = User
        fields = ( 
            'username',
            #'profile_img',
            #'header_img',
            'bio',
            'birth_date'
        )


class UserInfoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=50)
    user_id = serializers.CharField(min_length=4, max_length=15, validators= [UniqueValidator(queryset=User.objects.all())])
    # TODO add image field after setting image server
    # profile_img = serializers.ImageField(allow_null=True, allow_blank=True)
    # header_img = serializers.ImageField(allow_null=True, allow_blank=True)
    bio = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()
    birth_date = serializers.DateField(allow_null=True)
    
    tweets = serializers.SerializerMethodField()
    tweets_num = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    follower = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username',
            'user_id',
            # 'profile_img',
            # 'header_img',
            'bio',
            'created_at',
            'birth_date',
            'tweets',
            'tweets_num',
            'following',
            'follower'
        )

    def get_tweets(self, obj):
        tweets = obj.tweets.all().order_by('-written_at')
        serialized_tweets = TweetSerializer(tweets, read_only=True, many=True, context={'request': self.context['request']})
        return serialized_tweets.data

    def get_tweets_num(self, obj):
        return obj.tweets.all().count()

    def get_following(self, obj):
        return obj.follower.all().count()

    def get_follower(self, obj):
        return obj.following.all().count()

    # at least 4, at most 15 letters
    # only letters, digits, underscore(_) are allowed
    # https://help.twitter.com/ko/managing-your-account/change-twitter-handle
    def validate_user_id(self, value):
        
        if not (value.isalnum() or value.replace('_', '').isalnum()):
            raise serializers.ValidationError("your user_id should only contain letters, digits and underscore")
        if self.context['request'].user.user_id == value:
            raise serializers.ValidationError("your input is identical to your current user_id")

        return value

    def update(self, instance, validated_data):
        instance.user_id = validated_data.get('user_id', instance.user_id)
        return instance

      
class UserSearchInfoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=50)
    user_id = serializers.CharField(min_length=4, max_length=15, validators= [UniqueValidator(queryset=User.objects.all())])
    # TODO add image field after setting image server
    # profile_img = serializers.ImageField(allow_null=True, allow_blank=True)
    bio = serializers.CharField(allow_blank=True)
    tweets_num = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    follower = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username',
            'user_id',
            # 'profile_img',
            'bio',
            'tweets_num',
            'following',
            'follower'
        )

    def get_tweets(self, obj):
        tweets = obj.tweets.all()
        serialized_tweets = TweetSerializer(tweets, read_only=True, many=True, context={'request': self.context['request']})
        return serialized_tweets.data

    def get_tweets_num(self, obj):
        return obj.tweets.all().count()

    def get_following(self, obj):
        return obj.following.all().count()

    def get_follower(self, obj):
        return obj.follower.all().count()
