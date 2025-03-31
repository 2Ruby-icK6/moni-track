from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader

def unauthorized_user(view_func):
    def wrapper_func(request, *args, **kwags):
        if request.user.is_authenticated:
            return redirect('home')
        
        else:
            return view_func(request, *args, **kwags)
    
    return wrapper_func

def allowed_user(roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwags):
            
            group = None
            context = {}
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
            
            if group in roles:
                return view_func(request, *args, **kwags)
            
            else:
                html_template = loader.get_template('accounts/error/page-403.html')
                return HttpResponse(html_template.render(context, request))
                      
        return wrapper_func
    return decorator

def admin_only(view_func):
    def wrapper_func(request, *args, **kwags):
            
        group = None
        context = {}
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name
            
        if group == "Guest":
            return redirect("index_guest")
        
        if group == "Admin":
            return view_func(request, *args, **kwags)
        
        else: 
            html_template = loader.get_template('home/page-404.html')
            return HttpResponse(html_template.render(context, request))
        
    return wrapper_func