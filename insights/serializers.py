from rest_framework import serializers


class OverviewInsight(object):
    def __init__(self, overall_rank, category_rank, delta_reposts, delta_shares, delta_likes,
                 delta_visits):
        self.overall_rank = overall_rank
        self.category_rank = category_rank
        self.delta_reposts = delta_reposts
        self.delta_shares = delta_shares
        self.delta_likes = delta_likes
        self.delta_visits = delta_visits


class RepostAndShareInsights(object):
    def __init__(self, values, business_count, event_count):
        self.values = values
        self.business_count = business_count
        self.event_count = event_count


class LikeInsights(object):
    def __init__(self, values, users_count):
        self.values = values
        self.users_count = users_count


class SummaryInsights(object):
    def __init__(self, reposts_count, shares_count, likes_count, interactions):
        self.reposts_count = reposts_count
        self.shares_count = shares_count
        self.likes_count = likes_count
        self.interactions = interactions


class EventMomentInsightSerializer(serializers.Serializer):
    reposts_count = serializers.IntegerField()
    shares_count = serializers.IntegerField()
    participants_count = serializers.SerializerMethodField()

    def get_participants_count(self, moment):
        return moment.participants.count()


class OverviewInsightsSerializer(serializers.Serializer):
    overall_rank = serializers.IntegerField()
    category_rank = serializers.IntegerField()

    delta_reposts = serializers.FloatField()
    delta_shares = serializers.FloatField()
    delta_likes = serializers.FloatField()
    delta_visits = serializers.FloatField()


class RepostAndShareInsightsSerializer(serializers.Serializer):
    values = serializers.ListField(child=serializers.FloatField())
    business_count = serializers.IntegerField()
    event_count = serializers.IntegerField()


class LikeInsightsSerializer(serializers.Serializer):
    values = serializers.ListField(child=serializers.FloatField())
    users_count = serializers.IntegerField()


class SummaryInsightsSerializer(serializers.Serializer):
    reposts_count = serializers.IntegerField()
    shares_count = serializers.IntegerField()
    likes_count = serializers.IntegerField()
    interactions = serializers.ListSerializer(child=serializers.FloatField())
