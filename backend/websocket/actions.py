class SocketActions:
    MESSAGE = "message"

    # Use this in case the chat failed to be found maybe because deleted by blocked users
    CHAT_DOES_NOT_EXIST = "chat_does_not_exist"

    # Used to get the updated chat
    CHAT = "chat"

    USER_MENTION_MOMENT = "user_mention_moment"
    USER_FRIEND_REQUEST = "user_friend_request"

    USER_SPOT_REPLIES = "user_spot_replies"

    ALIGN_USER = "align_user"

    MATCH_CREATED = "match_created"
    MATCH_ONGOING = "match_ongoing"
    MATCH_REJECTED = "match_rejected"
    MATCH_COMPLETED = "match_completed"
