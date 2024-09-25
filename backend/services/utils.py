import ast
import os
import collections
from datetime import datetime
from django.conf import settings

import requests
from django.contrib.gis.geos import Point
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


def get_image_from_url(url):
    response = requests.get(url)
    temp_image = NamedTemporaryFile(delete=True)
    temp_image.write(response.content)
    temp_image.flush()

    return File(temp_image)


"""
    Used to format time_ago in stories
"""


def format_time_ago(created_at):
    timedelta = datetime.now().astimezone() - created_at

    minutes = int(timedelta.total_seconds() / 60)

    if minutes < 60:
        return f"{minutes}m"

    hours = round(minutes / 60)
    return f"{hours}h"


"""
    Use this functions instead of itertools.groupby because it requires that all the elements are consecutive.
"""


def groupby_unsorted(seq, key=lambda x: x):
    indexes = collections.defaultdict(list)
    for i, elem in enumerate(seq):
        indexes[key(elem)].append(i)
    for k, idxs in indexes.items():
        yield k, (seq[i] for i in idxs)


def normalize_id(id, type):
    if type == "venue":
        return int(str(id).replace("venue.story.", ""))


def cast_to_int(value):
    if value is not None and type(value) is str:
        cast_value = int(value)
        return cast_value
    return 0


def cast_to_bool(value):
    if value is None:
        return None
    return ast.literal_eval(value.capitalize())


def extract_keys(obj, keys):
    new_obj = {}

    for key in keys:
        new_obj[key] = obj[key]
    return new_obj


def array_int_to_string(slices):
    return [str(numeric_string) for numeric_string in slices]


def find_in(list, id):
    for x in list:
        if x.id == int(id):
            return x
    return None


def get_point_coordinate(coordinate):
    if isinstance(coordinate, list):
        return Point(coordinate, srid=4326)

    longitude = coordinate.get("longitude")
    latitude = coordinate.get("latitude")

    return Point([longitude, latitude], srid=4326)


def get_abstract_related_name(name):
    return f"%(app_label)s_%(class)s_{name}"


def remove_source_from_folder(path):
    source_path = os.path.join(settings.MEDIA_ROOT, path)

    if os.path.exists(source_path):
        os.remove(source_path)


def pop_or_none(key, object):
    if key in object:
        return object.pop(key)
    return None


def safe_list_get(array, index):
    try:
        return array[index]
    except IndexError:
        return None


def get_dict_keys(dictionary, keys):
    return {key: dictionary.get(key) for key in keys}


def omit_keys(dictionary, keys):
    for key in keys:
        if key in dictionary:
            dictionary.pop(key)


def update_for_object(object, data):
    for key, value in data.items():
        setattr(object, key, value)


def flatten_list(array):
    return [x["id"] for x in array]
