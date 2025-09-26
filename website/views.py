from django.shortcuts import render

# Create your views here.
def home (request):
    return render(request, 'home.html',{})

def pricing(request):
    return render(request, 'pricing.html',{}) 

def web_development(request):
    return render(request, 'web-development.html',{})

def user_research(request):
    return render(request, 'user-research.html',{})

def login(request):
    return render(request, 'login.html',{})

def register(request):
    return render(request, 'register.html',{})

def courseDetails(request):
    return render(request, 'courseDetails.html',{})
