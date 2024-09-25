import json
from json.decoder import JSONDecodeError

from authentication.api_views import (
    AuthenticationMixinAPIView,
    BusinessAuthenticationAPIView,
)

from business.models import Business
from core.querylimits import QueryLimits
from posts.models import BusinessPost, BusinessPostSlice, UserPost
from posts.serializers import (
    BusinessPostSerializer,
    CreatePostSerializer,
    CreateUserPostSerializer,
    UserPostSerializer,
)
from profiles.models import UserProfile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
)
from rest_framework.views import APIView
from services.utils import cast_to_int, pop_or_none


class PostAPIView(APIView):
    def iterate_slices(self, mode, post, data, count, model):
        slices = []
        invalid_slices = []

        for index in range(count):
            slice_data = data.get(f"data_{index}")

            if slice_data is None:
                continue

            try:
                slice_data = json.loads(slice_data)
                source = data.get(f"source_{index}")

                serializer = CreatePostSerializer(
                    data=slice_data, context={"model": model}
                )

                if serializer.is_valid():
                    new_data = {"post": post, "source": source}

                    slice = None

                    if mode == "create":
                        slice = serializer.save(**new_data)

                    if mode == "update":
                        slice_id = pop_or_none("id", slice_data)

                        if slice_id is None:
                            slice = serializer.save(**new_data)
                        else:
                            slice = serializer.update(slice_id)

                    if slice is not None:
                        slices.append(slice)
                    else:
                        invalid_slices.append(index)

            except JSONDecodeError:
                continue

        return slices, invalid_slices


class UserPostAPIView(AuthenticationMixinAPIView):
    def post(self, request):
        request_body = request.data

        source = request_body.get("source")
        json_data = request_body.get("data")
        data = json.loads(json_data)

        serializer = CreateUserPostSerializer(data={**data, "source": source})

        if serializer.is_valid():
            profile = request.user.profile

            post = serializer.save(profile)

            if post is None:
                return Response(status=HTTP_406_NOT_ACCEPTABLE)

            post = UserPostSerializer(post)

            return Response(post.data, status=HTTP_200_OK)

        elif "source" in serializer.errors:
            return Response(status=HTTP_406_NOT_ACCEPTABLE)

        return Response(status=HTTP_400_BAD_REQUEST)

    def put(self, request):
        request_body = request.data

        source = request_body.get("source", None)
        json_data = request_body.get("data")
        data = json.loads(json_data)

        post_id = data.pop("post_id")

        serializer = CreateUserPostSerializer(data={**data, "source": source})

        if serializer.is_valid():
            post = serializer.update(post_id, source)
            post = UserPostSerializer(post)

            return Response(post.data, status=HTTP_200_OK)

        return Response(status=HTTP_400_BAD_REQUEST)

    def get(self, request):
        user_id = request.query_params.get("user_id")

        try:
            profile = UserProfile.objects.get(user__uuid=user_id)
        except UserProfile.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        posts = UserPost.objects.filter(profile=profile)
        posts = UserPostSerializer(posts, many=True)

        return Response(posts.data, status=HTTP_200_OK)

    def delete(self, request):
        params = request.query_params
        post_id = params.get("post_id")

        UserPost.objects.filter(id=post_id).delete()

        return Response(status=HTTP_200_OK)


class BusinessPostAPIView(PostAPIView, BusinessAuthenticationAPIView):
    def get(self, request):
        posts = BusinessPost.objects.filter(business=request.business)
        posts = BusinessPostSerializer(posts, many=True)

        return Response(posts.data, status=HTTP_200_OK)

    def post(self, request):
        data = request.data

        meta_data = json.loads(data.get("data"))

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        count = meta_data.get("slices_count")
        post = BusinessPost.objects.create(business=request.business)
        slices, _ = self.iterate_slices("create", post, data, count, "business")

        if len(slices) == 0:
            post.delete()
            return Response(status=HTTP_406_NOT_ACCEPTABLE)

        post.set_ordering(slices)

        post = BusinessPostSerializer(post)
        return Response(post.data, status=HTTP_200_OK)

    def put(self, request):
        data = request.data

        meta_data = json.loads(data.get("data"))

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        post_id = meta_data.get("post_id")
        count = meta_data.get("slices_count")
        ordering = meta_data.get("ordering")

        try:
            post = BusinessPost.objects.get(id=post_id)
            slices, invalid_slices = self.iterate_slices(
                "update", post, data, count, "business"
            )

            post.update_ordering(slices, ordering, invalid_slices)

            post = BusinessPostSerializer(post)
            return Response(post.data, status=HTTP_200_OK)
        except BusinessPost.DoesNotExist:
            pass

        return Response(status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        params = request.query_params

        post_id = params.get("post_id")
        slice_id = params.get("id")

        if post_id is not None:
            BusinessPost.objects.filter(id=post_id).delete()

        if slice_id is not None:
            slice = BusinessPostSlice.objects.filter(id=slice_id).first()
            post = slice.post
            slice.delete()

            slices = BusinessPostSlice.objects.filter(post=post)

            if slices.count() == 0:
                post.delete()

        return Response(status=HTTP_200_OK)


@api_view(["GET"])
def get_business_posts(request):
    params = request.query_params

    uuid = params.get("id")

    try:
        business = Business.objects.get(uuid=uuid)
    except Business.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    offset = cast_to_int(params.get("offset"))
    up_offset = offset + QueryLimits.BUSINESS_POSTS

    posts = BusinessPost.objects.filter(business=business)[offset:up_offset]
    posts = BusinessPostSerializer(posts, many=True)

    return Response(posts.data, status=HTTP_200_OK)
