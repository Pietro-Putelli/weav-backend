from django.http import Http404, FileResponse


def serve_protected_file(request, path):
    try:
        file = open(f"/media/{path}", "rb")
        return FileResponse(file)
    except FileNotFoundError:
        raise Http404
