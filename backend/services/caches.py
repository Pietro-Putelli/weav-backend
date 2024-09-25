from django.core.cache import cache
import zlib
import json


def cache_object(obj, cache_key):
    compressed_all = zlib.compress(
        json.dumps(obj, separators=(",", ":")).encode("utf-8"), 9
    )
    cache.set(cache_key, compressed_all, timeout=None)


def cache_instance(instance, serializer, serializer_params={}):
    serialized_object = serializer(instance=instance, **serializer_params).data

    if hasattr(instance, "email"):
        email_key = instance.email
    else:
        email_key = instance.get("email")

    cache_object(serialized_object, email_key)
    return serialized_object


def get_object_from_cache(cache_key, delete=False):
    compressed_all = cache.get(cache_key)
    if compressed_all is None:
        return None

    if delete:
        delete_object_from_cache(cache_key)

    return json.loads(zlib.decompress(compressed_all).decode("utf-8"))


def delete_object_from_cache(cache_key):
    cache.delete(cache_key)
