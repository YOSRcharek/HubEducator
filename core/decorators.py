from django.shortcuts import redirect
from functools import wraps

def unauthenticated_user(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('unauthorized')  # Redirige si l'utilisateur est déjà connecté
        else:
            return view_func(request, *args, **kwargs)
    return wrapper
