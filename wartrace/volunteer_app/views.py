from django.shortcuts import render, redirect
from .models import Request, VolunteerViewedRequest
from authentication.decorators import login_required, volunteer

@login_required
@volunteer
def request_list(request):
    current_request = Request.objects.filter(status='in_search').exclude(viewed_requests__user=request.user.profile, volunteer=None).first()
    return render(request, 'volunteer_app/request_list.html', {'current_request': current_request})

@login_required
@volunteer
def accept_request(request, request_id):
    request_obj = Request.objects.get(id=request_id)
    user_profile = request.user.profile
    request_obj.volunteer = user_profile
    request_obj.status = "in_progress"
    request_obj.save()
    VolunteerViewedRequest.objects.get_or_create(user=user_profile, req=request_obj)
    return redirect('search')

@login_required
@volunteer
def reject_request(request, request_id):
    request_obj = Request.objects.get(id=request_id)
    VolunteerViewedRequest.objects.get_or_create(user=request.user.profile, req=request_obj)
    return redirect('search')
