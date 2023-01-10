from django.db import models
from django.db.models import CASCADE

from core.models import TimestampModel, DateOnlyModel
from insights.managers import EventInsightManager, BusinessInsightsManager

UNIQUE_USER_AND_BUSINESS = ("user", "business")
UNIQUE_USER_BUSINESS_AND_DATE = ("user", "business", "created_at")


class AbstractBusinessInsight(DateOnlyModel):
    user = models.ForeignKey("users.User", on_delete=CASCADE, db_index=False,
                             related_name="user_%(class)s")

    business = models.ForeignKey("business.Business", on_delete=CASCADE, db_index=False,
                                 related_name="business_%(class)s")

    objects = BusinessInsightsManager()

    class Meta:
        abstract = True
        unique_together = ("user", "business", "created_at")
        indexes = [models.Index(fields=["business", "created_at"])]


'''
    PROFILE VISITS
'''


class BusinessProfileVisit(AbstractBusinessInsight):
    pass


'''
    LIKES COUNT
'''


class BusinessLike(AbstractBusinessInsight):
    pass


'''
    REPOSTS
'''


class BusinessRepost(AbstractBusinessInsight):
    pass


'''
    SHARES
'''


class BusinessShare(AbstractBusinessInsight):
    pass


class AbstractEventInsight(DateOnlyModel):
    user = models.ForeignKey("users.User", on_delete=CASCADE, db_index=False,
                             related_name="%(app_label)s_%(class)s_user")

    event = models.ForeignKey("moments.EventMoment", on_delete=CASCADE,
                              related_name="%(app_label)s_%(class)s_event")

    objects = EventInsightManager()

    class Meta:
        abstract = True
        unique_together = ("user", "event", "created_at")
        indexes = [models.Index(fields=["event", "created_at"])]


class EventRepost(AbstractEventInsight):
    pass


class EventShare(AbstractEventInsight):
    pass
