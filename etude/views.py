from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import GroupeEtude
from django.conf import settings
from .models import GroupeEtude, Message
from django.http import JsonResponse

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
def rejoindre_groupe(request, groupe_id):
    groupe = get_object_or_404(GroupeEtude, pk=groupe_id)
    user = request.user

    # Vérifier si l'utilisateur n'est pas déjà membre
    if request.user not in groupe.membres.all():
        groupe.membres.add(request.user)

    # Retourner JSON pour l'AJAX
    return JsonResponse({
        "success": True,
        "groupe_id": groupe.id,
        "groupe_nom": groupe.nom
    })

@login_required
def etude_detail(request, groupe_id):
    groupe = get_object_or_404(GroupeEtude, pk=groupe_id)
    messages = groupe.messages.all().order_by('date_envoi')

    if request.method == "POST":
        contenu = request.POST.get("contenu")
        if contenu:
            Message.objects.create(groupe=groupe, auteur=request.user, contenu=contenu)
            return redirect('etude_detail', groupe_id=groupe.id)

    return render(request, 'etude/etude_detail.html', {
        'groupe': groupe,
        'messages': messages
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