from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from content.models import Marker


@login_required
def map_view(request):
    """
    Main map view showing all markers the user has access to.
    Actual marker data will be loaded via AJAX from the marker_api endpoint.
    """
    return render(request, 'map.html')
