from django.http import HttpResponse

def hello(request):
    return HttpResponse("Hello, world! This is the main app view.")

def register(request):
    return HttpResponse("This is the registration page.")