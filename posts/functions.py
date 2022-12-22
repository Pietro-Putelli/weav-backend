from business.models import Business
from core.querylimits import QueryLimits
from posts.models import BusinessPost, UserPost
from users.models import User


def get_user_posts(user_id, offset):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

    posts = UserPost.objects.filter(user=user)

    return posts[offset:offset + QueryLimits.USER_POSTS]


def get_business_posts(business_id, ordering, offset, limit):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return None

    posts = BusinessPost.objects.filter(business=business)

    if ordering == "older":
        posts = posts.order_by("created_at")

    return posts[offset:offset + limit]
