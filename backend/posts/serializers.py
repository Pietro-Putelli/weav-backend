from rest_framework import serializers

from services.images import moderate_image
from .models import BusinessPostSlice, UserPost
from django.db.models import Case, When, Value, IntegerField


FIELDS = ("id", "source", "title", "content", "created_at")

allow_blank = {"allow_blank": True, "allow_null": True}


class CreatePostSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, **allow_blank)
    content = serializers.CharField(required=False, **allow_blank)

    def save(self, post, source):
        post_slice = None

        post_slice = BusinessPostSlice.objects.create(
            post=post, source=source, **self.validated_data
        )

        return post_slice

    def update(self, slice_id, _=None):
        try:
            post_slice = BusinessPostSlice.objects.get(id=slice_id)

            validated_data = self.validated_data
            post_slice.title = validated_data.get("title", post_slice.title)
            post_slice.content = validated_data.get("content", post_slice.content)

            post_slice.save()

            return post_slice
        except BusinessPostSlice.DoesNotExist:
            return None


class BusinessPostSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPostSlice
        fields = FIELDS


class BusinessPostSerializer(serializers.Serializer):
    id = serializers.CharField()
    business_id = serializers.SerializerMethodField()
    slices = serializers.SerializerMethodField()

    def get_business_id(self, post):
        return post.business.uuid

    def get_slices(self, post):
        ordering = post.ordering

        if ordering is not None:
            ordering_ids = [int(id_) for id_ in ordering.split("-")]
        else:
            return []

        ordering_expression = Case(
            *[When(id=id_, then=pos) for pos, id_ in enumerate(ordering_ids)],
            default=Value(len(ordering_ids)),
            output_field=IntegerField()
        )

        slices = BusinessPostSlice.objects.filter(post=post).order_by(
            ordering_expression
        )

        return BusinessPostSliceSerializer(slices, many=True).data


class CreateBusinessPostSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPostSlice
        exclude = ("id", "post", "source")

    def create(self, validated_data):
        slice = BusinessPostSlice.objects.create(**validated_data)
        return slice

    def update(self, slice, validated_data):
        slice.title = validated_data.get("title")
        slice.content = validated_data.get("content")
        slice.save()


class CreateUserPostSerializer(serializers.ModelSerializer):
    source = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = UserPost
        fields = ("source", "title", "content")

    def validate_source(self, source):
        if source is None:
            return None

        return source

    def save(self, profile):
        post = UserPost.objects.create(profile=profile, **self.validated_data)

        is_image_valid = moderate_image(post.source.url)

        if not is_image_valid:
            post.delete()
            return None

        return post

    def update(self, post_id, source):
        try:
            post = UserPost.objects.get(id=post_id)

            validated_data = self.validated_data
            post.title = validated_data.get("title", post.title)
            post.content = validated_data.get("content", post.content)

            if source is not None:
                post.source = source

            post.save()

            return post
        except UserPost.DoesNotExist:
            return None


class UserPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPost
        fields = ("id", "source", "title", "content")
