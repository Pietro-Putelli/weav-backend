from django.db import models
from django.db.models import CASCADE
from core.models import TimestampModel
from core.fields import UniqueNameFileField

text_params = {"blank": True, "null": True}


class Post(TimestampModel):
    ordering = models.TextField(default="")

    def set_ordering(self, slices):
        ids = []

        for slice in slices:
            ids.append(str(slice.id))

        self.ordering = "-".join(ids)
        self.save()

    def update_ordering(self, slices, ordering, invalid_slices):
        if len(slices) > 0:
            ids = ordering.split("-")
            new_ids = []
            index = 0
            new_index = 0

            for id in ids:
                if "new" in id:
                    if not new_index in invalid_slices:
                        new_ids.append(str(slices[index].id))
                        index += 1

                    new_index += 1
                else:
                    new_ids.append(str(id))

            self.ordering = "-".join(new_ids)
        else:
            self.ordering = ordering

        self.save()


class PostSlice(TimestampModel):
    class Meta:
        abstract = True
        ordering = ["created_at"]

    title = models.CharField(max_length=32, **text_params)
    content = models.CharField(max_length=256, **text_params)


class UserPost(Post):
    user = models.ForeignKey(
        "users.User", related_name="user_post", on_delete=CASCADE)

    def __str__(self):
        return f"{self.id} • {self.user.username}"


def user_post_source_path(instance, filename):
    user = instance.post.user
    return f"{user.id}/posts/{filename}.png"


class UserPostSlice(PostSlice):
    post = models.ForeignKey(
        "UserPost", related_name="user_post", on_delete=CASCADE)

    source = UniqueNameFileField(upload_to=user_post_source_path)

    def __str__(self):
        return f"{self.post.user.username} • {self.post.id} • {self.title}"


'''
    BUSINESS
'''


class BusinessPost(Post):
    business = models.ForeignKey(
        "business.Business", related_name="business_post", on_delete=CASCADE)

    def __str__(self):
        return f"{self.id} • {self.business.name}"


def business_post_source_path(instance, filename):
    business = instance.post.business
    return f"{business.owner.id}/business/{business.id}/slices/{filename}.png"


class BusinessPostSlice(PostSlice):
    post = models.ForeignKey(
        "BusinessPost", related_name="business_post", on_delete=CASCADE)

    source = UniqueNameFileField(upload_to=business_post_source_path)

    def __str__(self):
        return f"{self.post.id} • {self.title}"
