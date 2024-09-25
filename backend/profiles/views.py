from django.db.models.query_utils import Q
from django.db.models import F
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
)
from rest_framework.views import APIView

from authentication.decorators import authentication_mixin
from core.querylimits import QueryLimits
from moments.models import UserMoment
from moments.serializers import UserMomentSerializer
from profiles.models import UserProfile, UserFriendRequest, UserFriend
from profiles.serializers import (
    ShortUserProfileSerializer,
    ShortUserProfileSerializer,
    UserFriendRequestSerializer,
    LongUserProfileSerializer,
)
from profiles.utils import get_chats_recent, handle_blocked_user
from services.images import moderate_image_bytes
from services.utils import cast_to_int
from users.models import User


class ProfileAPIView(APIView):
    def get(self, request):
        params = request.query_params

        user_id = params.get("user_id")
        username = params.get("username")

        try:
            my_profile = request.user.profile

            context = {"user": my_profile}

            if user_id is not None:
                profile = UserProfile.objects.get(user__uuid=user_id)
            else:
                profile = UserProfile.objects.get(username=username)

            profile = LongUserProfileSerializer(profile, context=context)

            return Response(profile.data, status=HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    def put(self, request):
        data = request.data
        user = request.user

        update_key = list(data.keys())[0]

        if update_key == "name":
            User.objects.filter(uuid=user.uuid).update(**data)
        else:
            UserProfile.objects.filter(user=user).update(**data)

        return Response(status=HTTP_200_OK)


@api_view(["PUT"])
def change_profile_picture(request):
    data = request.data
    user = request.user
    profile = user.profile

    picture = data.get("picture")

    is_source_valid = moderate_image_bytes(picture)

    if is_source_valid:
        profile.set_picture(picture)
        return Response({"picture": profile.picture.url}, status=HTTP_200_OK)

    return Response(status=HTTP_406_NOT_ACCEPTABLE)


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

    def put(self, request):
        uuid = request.data.get("id")

        my_profile = request.user.profile
        blocked_users = my_profile.blocked_users

        try:
            profile = UserProfile.objects.get(user__uuid=uuid)
        except UserProfile.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        # I'm blocking the user
        if profile not in blocked_users.all():
            blocked_users.add(profile)
            handle_blocked_user(my_profile, profile)
        else:
            blocked_users.remove(profile)

        return Response(status=HTTP_200_OK)


@api_view(["GET"])
def search_users(request):
    params = request.query_params

    profile = request.user.profile
    blocked_users = profile.blocked_users.all()

    value = params.get("value", "")
    offset = cast_to_int(params.get("offset"))
    up_offset = offset + QueryLimits.SEARCH_USERS

    users = UserProfile.objects.filter(
        Q(username__icontains=value)
        & ~Q(blocked_users__in=[profile])
        & ~Q(id=profile.id)
    ).exclude(id__in=blocked_users)[offset:up_offset]

    users = ShortUserProfileSerializer(users, many=True).data
    return Response(users, status=HTTP_200_OK)


class UserFeedAPIView(APIView):
    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))
        up_offset = offset + QueryLimits.USER_FEEDS

        profile = request.user.profile

        moments = UserMoment.objects.get_moments_where_im_tagged(profile)[
            offset:up_offset
        ]

        context = {"user": request.user}

        moments = UserMomentSerializer(moments, many=True, context=context)

        return Response(moments.data, status=HTTP_200_OK)

    def delete(self, request):
        moment_id = request.query_params.get("id")

        try:
            moment = UserMoment.objects.get(uuid=moment_id)
            moment.participants.remove(request.user.profile)

            return Response(status=HTTP_200_OK)
        except UserMoment.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


"""
    FRIENDSHIP STATES:
        1. NONE => create friend request
        2. FRIEND => Delete friend UserFriend entry
        3. MY_REQUEST => delete friend request
        4. USER_REQUEST => accept user friend request and create UserFriend entry
"""


class UserFriendRequestAPIView(APIView):
    def post(self, request):
        data = request.data
        uuid = data.get("id")

        profile = request.user.profile

        try:
            friend = UserProfile.objects.get(user__uuid=uuid)
        except UserProfile.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        params = {"user": profile, "friend": friend}

        request_queryset = UserFriendRequest.objects
        friend_queryset = UserFriend.objects

        # Case 2 => If friend exists, delete it
        deleted = friend_queryset.delete_if_friends(profile, friend)

        if deleted:
            return Response(status=HTTP_200_OK)

        friend_request = request_queryset.filter(**params)

        if friend_request.exists():
            # Case 3 => Delete existing friendship request

            friend_request.delete()
            return Response(status=HTTP_200_OK)

        comp_request = request_queryset.filter(user=friend, friend=profile)

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

        my_profile = request.user.profile

        requests = UserFriendRequest.objects.filter(friend=my_profile)[offset:limit]
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

        friends, count = UserFriend.objects.get_friends(request.user.profile)
        friends = friends[offset:limit]
        friends = ShortUserProfileSerializer(friends, many=True)

        return Response({"friends": friends.data, "count": count}, status=HTTP_200_OK)


"""
    Recent users are:
        -> recent chats
        -> friends
"""


@api_view(["GET"])
def get_recent_users(request):
    profile = request.user.profile
    users = get_chats_recent(profile)
    users = ShortUserProfileSerializer(users, many=True)

    return Response(users.data, status=HTTP_200_OK)


@api_view(["PUT"])
@authentication_mixin
def update_profile_language(request):
    language = request.data.get("language")

    user = request.user
    user.language = language
    user.save()

    return Response(status=HTTP_200_OK)
