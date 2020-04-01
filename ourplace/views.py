from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import pickle
import base64
import numpy
import json
from itertools import zip_longest

import static.constants.colours as palettes


context_dict = {}
from django.contrib.auth.models import User
from ourplace.models import Canvas, UserProfile, CanvasAccess
from ourplace.forms import CanvasForm, CanvasEditForm, CanvasAccessForm

def index(request):
    response = render(request, 'ourplace/index.html')
    return response

def about(request):
    return render(request, 'ourplace/about.html', context=context_dict)

def faq(request):
    return render(request, 'ourplace/faq.html')

@login_required
def account(request):
    return render(request, 'ourplace/account.html')

def user(request, username):
    context_dict = {}

    try:
        target_user = User.objects.get(username=username)
        context_dict['target_users_places'] = Canvas.objects.filter(owner=target_user).order_by('-views')
        context_dict['num_target_users_places'] = len(context_dict['target_users_places'])
        context_dict['target_user_total_views'] = context_dict['target_users_places'].aggregate(Sum('views'))['views__sum']
        context_dict['target_user'] = target_user
        # context_dict['target_user_profile'] = UserProfile.objects.get(user=target_user)
    except User.DoesNotExist:
        context_dict['target_user'] = None

    return render(request, 'ourplace/user.html', context=context_dict)

@login_required
def create_place(request):
    form = CanvasForm()
    context_dict = {}

    # do we have a http post
    if request.method == 'POST':
        form = CanvasForm(request.POST)

        # is the form valid
        if form.is_valid():
            canvas = form.save(commit=False)
            canvas.owner = request.user
            canvas.save()
            return redirect(reverse('ourplace:view_place', args=[canvas.slug]))
        # else:
        #     print(form.errors)

    # This is needed to allow the form to automagically display in two columns
    context_dict['form'] = list(zip_longest(*[iter(form)]*2))

    return render(request, 'ourplace/create_place.html', context=context_dict)

@login_required
def edit_place(request, place_name_slug):
    # context dict: 'form' is the form, 'error' is a general error
    # first, make sure there's a canvas
    if Canvas.objects.filter(slug=place_name_slug).exists():
        canvas = Canvas.objects.get(slug=place_name_slug)
        # check if the currently logged in user is the owner
        if request.user == canvas.owner:
            # if everything is correct and the settings can be edited

            # add the canvas title to the context dict
            context_dict['canvas_title'] = canvas.title
            context_dict['canvas_slug'] = canvas.slug

            # deal with the form
            form = CanvasEditForm()
            context_dict['form'] = form
            if request.method == 'POST':
                form = CanvasEditForm(request.POST)
                if form.is_valid():
                    canvasquery = Canvas.objects.filter(slug=place_name_slug)
                    canvasquery.update(cooldown=form.cleaned_data['cooldown'])
                    canvasquery.update(visibility=form.cleaned_data['visibility'])
                    return redirect(reverse('ourplace:view_place', args=[canvas.slug]))

                else:
                    print(form.errors)
        else:
            # if the current user doesn't have access, but the canvas exits and is private
            context_dict['error'] = "You do not own this canvas, you can't edit settings for a canvas you don't own."
    else:
        context_dict['error'] = "Canvas does not exist."

    return render(request, 'ourplace/edit_place.html', context=context_dict)

@login_required
def access_place(request, place_name_slug):
    # view for the form that adds/removes entries in the canvas access table which dictates if a user can acess a canvas
    # context dict: 'form' is the form, 'error' is a general error, 'form_error' is an error with the form to be put out
    # with the form, 'current_access' is a list of strings that are the usernames that currently have access

    # make sure there's a canvas in the first place
    if Canvas.objects.filter(slug=place_name_slug).exists():
        canvas = Canvas.objects.get(slug=place_name_slug)
        # checks if the canvas is private, then if the currently logged in user is the owner
        if canvas.visibility == Canvas.PUBLIC:
            context_dict['error'] = "Canvas is public, you can't edit access for a public canvas."
        elif request.user == canvas.owner:
            # if everything is correct and the access can be edited

            # this generates a list of users that currently have access and stores it in the context dict under 'current_access'
            current_users_objects= CanvasAccess.objects.filter(canvas=canvas)
            current_users =             []
            for use in current_users_objects:
                current_users.append(use.user.username)
            context_dict['current_access'] = current_users

            # add the canvas title to the context dict
            context_dict['canvas_title'] = canvas.title

            # then we handle the form
            form = CanvasAccessForm()
            context_dict['form'] = form
            if request.method == 'POST':
                form = CanvasAccessForm(request.POST)
                if form.is_valid():
                    # check if the provided username maps to a valid user
                    if User.objects.filter(username=form.cleaned_data['username']).exists():
                        newuser = User.objects.get(username=form.cleaned_data['username'])
                        # if the username and canvas mapping don't already exist then make a new one, if it already exists then delete it
                        if not CanvasAccess.objects.filter(user=newuser).filter(canvas=canvas).exists():
                            canvasaccess = form.save(commit=False)
                            canvasaccess.user = newuser
                            canvasaccess.canvas = canvas
                            canvasaccess.save()
                        else:
                            CanvasAccess.objects.get(user = newuser, canvas=canvas).delete()
                    else:
                        context_dict['form_error'] = "User not found."
                else:
                    print(form.errors)
        else:
            # if the current user doesn't have access, but the canvas exits and is private
            context_dict['error'] = "You do not own this canvas, you can't edit access for a canvas you don't own."
    else:
        context_dict['error'] = "Canvas does not exist."
    return render(request, 'ourplace/access_place.html', context=context_dict)

def view_place(request, place_name_slug):

    try:
        canvas = Canvas.objects.get(slug=place_name_slug)
        # if public or owner, or on canvas acess
        if request.user.is_authenticated and (canvas.visibility == Canvas.PUBLIC or request.user == canvas.owner or  CanvasAccess.objects.filter(user=request.user).filter(canvas=canvas).exists()):
            context_dict['canvas'] = canvas
            context_dict['is_auth'] = True
        else:
            # tell the page that it isn't authorised
            context_dict['is_auth'] = False

        Canvas.objects.filter(slug=place_name_slug).update(views=canvas.views+1)
    except Canvas.DoesNotExist:
        context_dict['canvas'] = None


    palette = palettes.palette1
    context_dict['palette'] = palette



    return render(request, 'ourplace/view_place.html', context=context_dict)


def search(request):
    context_dict = {}

    if request.GET.get('q', False):
        search_string = request.GET['q']
        context_dict['has_searched'] = True
        context_dict['search_results'] = Canvas.objects.filter(title__contains=search_string)
        context_dict['num_results'] = len(context_dict['search_results'])
        context_dict['search_string'] = search_string

    try:
        if (request.user.is_authenticated):
            context_dict['users_places'] = Canvas.objects.filter(owner=request.user)
            context_dict['num_user_places'] = len(context_dict['users_places'])

        context_dict['popular_places'] = Canvas.objects.order_by('-views')[:8]
    except Canvas.DoesNotExist:
        context_dict['user_places'] = {}
    return render(request, 'ourplace/search.html', context=context_dict)

def download_bitmap(request, place_name_slug):
    response = {}
    try:
        canvas = Canvas.objects.get(slug=place_name_slug)
        bitmap_bytes = base64.b64decode(canvas.bitmap)
        bitmap_array = pickle.loads(bitmap_bytes)
        response['bitmap'] = bitmap_array.tolist()
    except Canvas.DoesNotExist:
        raise Http404("Place not found..")

    return HttpResponse(json.dumps(response), content_type="application/json")
