from django.shortcuts import render


def marker_create_view(request):
    return render(request, 'marker-create.html')


def marker_detail_view(request, pk):
    return render(request, 'marker-detail.html')


def annotation_create_view(request):
    return render(request, 'annotation-form.html')
