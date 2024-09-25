import functools


def decorate_method(dec_for_function):
    def dec_for_method(unbounded_method):
        def decorated_unbounded_method(self, *args, **kwargs):
            @dec_for_function
            def bounded_method(*args, **kwargs):
                return unbounded_method(self, *args, **kwargs)

            return bounded_method(*args, **kwargs)

        return decorated_unbounded_method

    return dec_for_method


def composed(*decs):
    def deco(f):
        for dec in reversed(decs):
            f = dec(f)
        return f

    return deco


def disable_test(disabled=False):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if disabled:
                return
            return func(*args, **kwargs)

        return wrapper

    return actual_decorator
