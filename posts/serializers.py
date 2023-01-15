from rest_framework import serializers

from shared.models import MiddleSource
from .models import BusinessPostSlice, UserPostSlice

FIELDS = ("id", "source", "title", "content", "created_at")


class CreatePostSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_null=True)
    content = serializers.CharField(required=False, allow_null=True)

    def _get_model(self):
        context_model = self.context.get("model")

        if context_model == "business":
            return BusinessPostSlice

        return UserPostSlice

    def save(self, post, source):
        model = self._get_model()

        middle_source = MiddleSource.objects.create(source=source)

        slice = None

        if middle_source.is_valid():
            slice = model.objects.create(post=post, source=source, **self.validated_data)

        return slice

    def update(self, slice_id, _=None):

        model = self._get_model()

        try:
            slice = model.objects.get(id=slice_id)

            validated_data = self.validated_data
            slice.title = validated_data.get("title", slice.title)
            slice.content = validated_data.get("content", slice.content)

            slice.save()

            return slice
        except model.DoesNotExist:
            return None


class PostSerializer(serializers.Serializer):
    id = serializers.CharField()
    ordering = serializers.CharField()


class UserPostSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPostSlice
        fields = FIELDS


class UserPostSerializer(PostSerializer):
    user_id = serializers.SerializerMethodField()
    slices = serializers.SerializerMethodField()

    def get_user_id(self, post):
        return post.user.uuid

    def get_slices(self, post):
        slices = UserPostSlice.objects.filter(post=post)
        return UserPostSliceSerializer(slices, many=True).data


class BusinessPostSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPostSlice
        fields = FIELDS


class BusinessPostSerializer(PostSerializer):
    business_id = serializers.SerializerMethodField()
    slices = serializers.SerializerMethodField()

    def get_business_id(self, post):
        return post.business.uuid

    def get_slices(self, post):
        slices = BusinessPostSlice.objects.filter(post=post)
        return BusinessPostSliceSerializer(slices, many=True).data


class CreatePostSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPostSlice
        exclude = ("id", "post", "source")

    def update(self, slice, validated_data):
        slice.title = validated_data.get("title")
        slice.content = validated_data.get("content")
        slice.save()


class CreateUserPostSliceSerializer(CreatePostSliceSerializer):

    def create(self, validated_data):
        slice = UserPostSlice.objects.create(**validated_data)
        return slice


class CreateBusinessPostSliceSerializer(CreatePostSliceSerializer):

    def create(self, validated_data):
        slice = BusinessPostSlice.objects.create(**validated_data)
        return slice
