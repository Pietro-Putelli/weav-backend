from core.fields import UniqueNameFileField
from core.models import TimestampModel
from django.db import models
from django.db.models import CASCADE

allow_blank = {"blank": True, "null": True}


def user_post_source_path(post, filename):
    user = post.profile.user
    return f"users/{user.uuid}/posts/{filename}.png"


class UserPost(TimestampModel):
    profile = models.ForeignKey(
        "profiles.UserProfile", related_name="user_post", on_delete=CASCADE
    )

    source = UniqueNameFileField(upload_to=user_post_source_path)

    title = models.CharField(max_length=32, **allow_blank)
    content = models.CharField(max_length=256, **allow_blank)

    def __str__(self):
        return f"{self.id} • {self.profile.username}"


"""
    BUSINESS
"""


class BusinessPost(TimestampModel):
    business = models.ForeignKey(
        "business.Business", related_name="business_post", on_delete=CASCADE
    )

    ordering = models.TextField(default="", **allow_blank)

    def set_ordering(self, slices):
        ids = []

        for slice in slices:
            slice_id = str(slice.id)

            if not "new" in slice_id:
                ids.append(slice_id)

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

    def __str__(self):
        return f"{self.id} • {self.business.name}"


def business_post_source_path(instance, filename):
    business = instance.post.business
    return f"users/{business.owner.user.uuid}/business/{business.uuid}/slices/{filename}.png"


class BusinessPostSlice(TimestampModel):
    class Meta:
        ordering = ["created_at"]

    post = models.ForeignKey(
        "BusinessPost", related_name="business_post", on_delete=CASCADE
    )

    source = UniqueNameFileField(upload_to=business_post_source_path)

    title = models.CharField(max_length=32, **allow_blank)
    content = models.CharField(max_length=256, **allow_blank)

    def __str__(self):
        return f"{self.post.id} • {self.title}"
