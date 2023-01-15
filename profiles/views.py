from django.db.models.query_utils import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_406_NOT_ACCEPTABLE
from rest_framework.views import APIView

from core.authentication import AuthenticationMixinAPIView
from core.querylimits import QueryLimits
from devices.models import Device
from moments.models import UserMoment
from moments.serializers import UserMomentSerializer
from pp_placehoder.generator import generate_profile_placeholder
from profiles.models import UserProfile, UserFriendRequest, UserFriend
from profiles.serializers import ShortUserProfileSerializer, ShortProfileSerializer, \
    UserChatProfileSerializer, ShortUserProfileChatSerializer, UserFriendRequestSerializer
from profiles.utils import get_chats_recent, handle_blocked_user
from servicies.utils import cast_to_int, flatten_list
from shared.models import MiddleSource, UserInterest
from shared.serializers import CreatePhoneSerializer, StaticFeatureSerializer
from users.models import User


class ProfileAPIView(AuthenticationMixinAPIView):
    def get(self, request):
        user_id = request.query_params.get("id")

        try:
            profile = UserProfile.objects.get(user__uuid=user_id)
            user = request.user

            if isinstance(user, User):
                profile = UserChatProfileSerializer(profile, context={"user": user})
            else:
                profile = ShortProfileSerializer(profile)

            return Response(profile.data, status=HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    def post(self, request):
        form_data = request.data
        picture = form_data.get("picture")

        profile = request.user.profile
        profile.set_picture(picture)

        return Response({"picture": profile.picture.url}, status=HTTP_200_OK)

    def put(self, request):
        data = request.data
        user = request.user

        update_key = list(data.keys())[0]

        if update_key == "interests":
            my_interests = data.get("interests")
            interests = UserInterest.objects.filter(id__in=my_interests)

            if interests.count() > 0:
                user.profile.set_interests(interests)
        elif update_key == "username":
            User.objects.filter(uuid=user.uuid).update(**data)
        elif update_key == "phone":
            phone_data = data.get("phone")
            serializer = CreatePhoneSerializer(data=phone_data)
            if serializer.is_valid():
                UserProfile.objects.filter(user=user).update(phone=serializer.validated_data)
        else:
            UserProfile.objects.filter(user=user).update(**data)

        return Response(status=HTTP_200_OK)


'''
    Get profile info such as requests_count and moments_count
'''


@api_view(["GET"])
def get_profile_info(request):
    user = request.user

    requests = UserFriendRequest.objects.filter(friend=user).values("id")
    moments = UserMoment.objects.get_moments_where_im_tagged(user).values("id")

    requests = flatten_list(requests)
    moments = flatten_list(moments)

    return Response({"requests": list(requests), "moments": list(moments)}, status=HTTP_200_OK)


@api_view(["PUT"])
def update_user_password(request):
    user = request.user
    data = request.data

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if len(new_password) >= 8:
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()

            return Response(status=HTTP_200_OK)

    return Response(status=HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def change_profile_picture(request):
    data = request.data
    profile = request.user.profile

    status = HTTP_200_OK

    # Removing current picture and create placeholder
    if "picture" not in data:
        picture = generate_profile_placeholder(profile.name)
        profile.set_picture(picture)
    else:
        picture = data.get("picture")

        middle_picture = MiddleSource.objects.create(source=picture)

        status = HTTP_406_NOT_ACCEPTABLE

        if middle_picture.is_valid():
            profile.set_picture(picture)
            status = HTTP_200_OK

    return Response({"picture": profile.picture.url}, status=status)


class ProfileSettings(APIView):
    def post(self, request):
        settings = request.data.get("settings")
        UserProfile.objects.filter(user=request.user).update(settings=settings)
        return Response(status=HTTP_200_OK)


class BlockUser(APIView):
    def get(self, request):
        my_profile = request.user.profile
        users = my_profile.blocked_users.all()

        users = ShortUserProfileSerializer(users, many=True).data
        return Response(users, status=HTTP_200_OK)

    def post(self, request):
        data = request.data

        uuid = request.query_params.get("id")
        mode = data.get("mode")

        my_profile = request.user.profile
        user = User.objects.get(uuid=uuid)

        if mode == "block":
            my_profile.blocked_users.add(user)
            handle_blocked_user(request.user, user)

        if mode == "unblock":
            my_profile.blocked_users.remove(user)

        return Response(status=HTTP_200_OK)


@api_view(["GET"])
def search_users(request):
    params = request.query_params

    user = request.user

    value = params.get("value")
    offset = cast_to_int(params.get("offset"))
    up_offset = offset + QueryLimits.SEARCH_USERS

    users = UserProfile.objects.filter(
        Q(user__username__icontains=value) & ~Q(blocked_users__in=[user]) & ~Q(user=user))[
            offset: up_offset]

    users = ShortProfileSerializer(users, many=True).data
    return Response(users, status=HTTP_200_OK)


@api_view(["PUT"])
def set_device_token(request):
    data = request.data
    token = data.get("token")

    Device.objects.update_or_create(user=request.user, token=token)

    return Response(status=HTTP_200_OK)


class UserFeedAPIView(APIView):
    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))
        up_offset = offset + QueryLimits.USER_FEEDS

        moments = UserMoment.objects.get_moments_where_im_tagged(request.user)[offset:up_offset]
        moments = UserMomentSerializer(moments, many=True)

        return Response(moments.data, status=HTTP_200_OK)

    def delete(self, request):
        moment_id = request.query_params.get("id")

        try:
            moment = UserMoment.objects.get(uuid=moment_id)
            moment.users_tag.remove(request.user)

            return Response(status=HTTP_200_OK)
        except UserMoment.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


'''
    FRIENDSHIP STATES:
        1. NONE => create friend request
        2. FRIEND => Delete friend UserFriend entry
        3. MY_REQUEST => delete friend request
        4. USER_REQUEST => accept user friend request and create UserFriend entry
'''


class UserFriendRequestAPIView(APIView):
    def post(self, request):
        data = request.data
        uuid = data.get("id")

        user = request.user

        try:
            friend = User.objects.get(uuid=uuid)
        except User.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        params = {"user": user, "friend": friend}

        request_queryset = UserFriendRequest.objects
        friend_queryset = UserFriend.objects

        # Case 2 => If friend exists, delete it
        deleted = friend_queryset.delete_if_friends(user, friend)

        if deleted:
            return Response(status=HTTP_200_OK)

        friend_request = request_queryset.filter(**params)

        if friend_request.exists():
            # Case 3 => Delete existing friendship request

            friend_request.delete()
            return Response(status=HTTP_200_OK)

        comp_request = request_queryset.filter(user=friend, friend=user)

        if comp_request.exists():
            # Case 4 => Accept request, delete entry and create UserFriend entry

            comp_request.delete()
            friend_queryset.create(**params)
        else:
            # Case 1 => No relationship between the users, create new friend request

            request_queryset.create(**params)

        return Response(status=HTTP_200_OK)

    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))
        limit = cast_to_int(params.get("limit"))

        requests = UserFriendRequest.objects.filter(friend=request.user)[offset:limit]
        requests = UserFriendRequestSerializer(requests, many=True)

        return Response(requests.data, status=HTTP_200_OK)

    def delete(self, request):
        request_id = request.query_params.get("request_id")

        UserFriendRequest.objects.filter(id=request_id).delete()

        return Response(status=HTTP_200_OK)


class UserFriendAPIView(APIView):
    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))
        limit = cast_to_int(params.get("limit")) + offset

        friends, count = UserFriend.objects.get_friends(request.user)
        friends = friends[offset:limit]
        friends = ShortUserProfileSerializer(friends, many=True)

        return Response({"friends": friends.data, "count": count}, status=HTTP_200_OK)


'''
    Recent users are:
        -> recent chats
        -> friends
'''


@api_view(["GET"])
def get_recent_users(request):
    users = get_chats_recent(request.user)
    users = ShortUserProfileChatSerializer(users, many=True)

    return Response(users.data, status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_interests_list(request):
    interests = UserInterest.objects.all()
    interests = StaticFeatureSerializer(interests, many=True)

    return Response(interests.data, status=HTTP_200_OK)
