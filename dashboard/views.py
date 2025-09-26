from django.shortcuts import render

# Create your views here.
def dashboard (request):
    return render(request, 'dashboard.html',{})

def users (request):
    return render(request, 'users/users.html',{})

def adduser (request):
    return render(request, 'users/adduser.html',{})