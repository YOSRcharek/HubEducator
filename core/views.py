from django.shortcuts import render

def unauthorized (request):
    return render(request, 'unauthorized.html',{})

def profil (request):
    return render(request, 'profil.html',{})

