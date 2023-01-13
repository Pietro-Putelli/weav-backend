from core.querylimits import QueryLimits
from posts.models import UserPost
from users.models import User


def get_user_posts(user_id, offset):
    try:
        user = User.objects.get(uuid=user_id)
    except User.DoesNotExist:
        return None

    posts = UserPost.objects.filter(user=user)

    return posts[offset:offset + QueryLimits.USER_POSTS]
