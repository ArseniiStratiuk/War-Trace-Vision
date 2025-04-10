from django.shortcuts import redirect
from functools import wraps

def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # You can log or show a message here
            return redirect('login')  # Or use reverse('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def volunteer(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        print()
        if not request.user.profile.category == 'volunteer':
            print('if')
            return redirect('bad_category')  # Or use reverse('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
