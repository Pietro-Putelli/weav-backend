import json
from json.decoder import JSONDecodeError

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, \
    HTTP_406_NOT_ACCEPTABLE
from rest_framework.views import APIView

from business.authentication import BusinessAuthenticationAPIView
from business.models import Business
from core.authentication import AuthenticationMixinAPIView
from core.querylimits import QueryLimits
from posts.functions import get_user_posts
from posts.models import UserPost, BusinessPost, UserPostSlice, BusinessPostSlice
from posts.serializers import BusinessPostSerializer, UserPostSerializer, CreatePostSerializer
from servicies.utils import cast_to_int, pop_or_none


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

                serializer = CreatePostSerializer(data=slice_data, context={"model": model})

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


class UserPostAPIView(PostAPIView, AuthenticationMixinAPIView):

    def post(self, request):
        data = request.data

        meta_data = json.loads(data.get("data"))

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        count = meta_data.get("slices_count")
        post = UserPost.objects.create(user=request.user)
        slices, _ = self.iterate_slices("create", post, data, count, "user")

        if len(slices) == 0:
            post.delete()
            return Response(status=HTTP_406_NOT_ACCEPTABLE)

        post.set_ordering(slices)

        post = UserPostSerializer(post)
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
            post = UserPost.objects.get(id=post_id)
            slices, invalid_slices = self.iterate_slices("update", post, data, count, "user")

            post.update_ordering(slices, ordering, invalid_slices)

            if len(slices) == 0 and len(invalid_slices) != 0:
                return Response(status=HTTP_406_NOT_ACCEPTABLE)

            post = UserPostSerializer(post)
            return Response(post.data, status=HTTP_200_OK)
        except UserPost.DoesNotExist:
            pass

        return Response(status=HTTP_400_BAD_REQUEST)

    def get(self, request):
        params = request.query_params
        user_id = params.get("user_id")
        offset = cast_to_int(params.get("offset"))

        posts = get_user_posts(user_id, offset)
        posts = UserPostSerializer(posts, many=True)

        return Response(posts.data, status=HTTP_200_OK)

    def delete(self, request):
        params = request.query_params

        post_id = params.get("post_id")
        slice_id = params.get("id")

        if post_id is not None:
            UserPost.objects.filter(id=post_id).delete()

        if slice_id is not None:
            slice = UserPostSlice.objects.filter(id=slice_id).first()
            post = slice.post
            slice.delete()

            slices = UserPostSlice.objects.filter(post=post)

            if slices.count() == 0:
                post.delete()

        return Response(status=HTTP_200_OK)


class BusinessPostAPIView(PostAPIView, BusinessAuthenticationAPIView):
    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))
        up_offset = offset + QueryLimits.MY_BUSINESS_POSTS
        ordering = params.get("ordering")

        posts = BusinessPost.objects.filter(business=request.business)
        if ordering == "older":
            posts = posts.order_by("created_at")

        posts = posts[offset:up_offset]
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
            slices, invalid_slices = self.iterate_slices("update", post, data, count, "business")

            post.update_ordering(slices, ordering, invalid_slices)

            if len(slices) == 0 and len(invalid_slices) != 0:
                return Response(status=HTTP_406_NOT_ACCEPTABLE)

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
