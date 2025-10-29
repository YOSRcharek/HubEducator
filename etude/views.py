from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import GroupeEtude
from django.http import JsonResponse, Http404
from django.db.models import Q
from django.urls import reverse

@login_required
def etude_list(request):
    """
    Page to display all study groups.
    """
    groupes = GroupeEtude.objects.all()
    return render(request, 'etude/etude_list.html', {'groupes': groupes})


@login_required
def creer_groupe(request):
    """
    Page to create a new study group.
    """
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')

        if nom:
            GroupeEtude.objects.create(
                nom=nom,
                description=description,
                createur=request.user
            )
            return redirect('etude_list')

    return render(request, 'etude/creer_groupe.html')

@login_required
def join_group(request, group_id):
    # only accept POST to join
    if request.method != "POST":
        return redirect('etude_list')

    groupe = get_object_or_404(GroupeEtude, id=group_id)
    if request.user not in groupe.membres.all():
        groupe.membres.add(request.user)
        messages.success(request, "You have joined the group.")
    else:
        messages.info(request, "You are already a member of this group.")

    # After joining, go to the group's detail page so member list shows you
    return redirect('etude_detail', groupe_id=group_id)

@login_required
def etude_detail(request, groupe_id):
    """
    Strict access: only creator, members, or staff may view.
    Non-authorized users get 404 (so the URL appears non-existent).
    """
    # fetch the group by id first
    groupe = get_object_or_404(GroupeEtude, pk=groupe_id)

    user = request.user
    # allow if user is staff, creator, or a member
    if not (user.is_staff or user == groupe.createur or groupe.membres.filter(pk=user.pk).exists()):
        # hide existence for unauthorized users
        raise Http404()

    # load group related data for the template
    messages_list = groupe.messages.all().order_by('date_envoi')
    resources = groupe.resources_etude.all() if hasattr(groupe, 'resources_etude') else None

    return render(request, 'etude/etude_detail.html', {
        'groupe': groupe,
        'messages': messages_list,
        'resources': resources,
    })

@login_required
def get_messages(request, groupe_id):
    groupe = get_object_or_404(GroupeEtude, pk=groupe_id)
    messages = groupe.messages.all().order_by('date_envoi')

    data = [
        {
            "auteur": msg.auteur.username,
            "contenu": msg.contenu,
            "date": msg.date_envoi.strftime("%d/%m/%Y %H:%M")
        }
        for msg in messages
    ]
    return JsonResponse({"messages": data})