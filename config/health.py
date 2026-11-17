from django.http import HttpResponse


def saude(request):
    return HttpResponse('ok', content_type='text/plain')
