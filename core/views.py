from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.utils.crypto import encrypt_file
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from .forms import UserRegistrationForm
from .models import Service, Poste, StatutChoices
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import *
from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import re
from django.http import HttpResponse
from core.utils.crypto import decrypt_file
from .forms import *  # À créer si tu veux un formulaire Django, sinon utilise request.POST


@login_required
def download_piece(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    encrypted_data = piece.fichier.read()
    decrypted_data = decrypt_file(encrypted_data)
    response = HttpResponse(decrypted_data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{piece.fichier.name}"'
    return response

def is_admin_or_chef(user):
    return user.est_admin or (user.poste and user.poste.est_chef)


@login_required
@user_passes_test(is_admin_or_chef)
def user_activate(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        try:
            user.statut = 'actif'
            user.save()
            messages.success(request, f"Le compte de {user.prenom} {user.nom} a été activé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'activation du compte : {str(e)}")
    
    return redirect('users')

@login_required
@user_passes_test(is_admin_or_chef)
def user_deactivate(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        try:
            user.statut = 'desactive'
            user.save()
            # Libérer le poste occupé
            if user.poste:
                user.poste.est_occupe = False
                user.poste.save()
            messages.success(request, f"Le compte de {user.prenom} {user.nom} a été désactivé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la désactivation du compte : {str(e)}")
    return redirect('users')

@login_required
@user_passes_test(is_admin_or_chef)
def user_create(request):
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            email = request.POST.get('email')
            matricule = request.POST.get('matricule') 
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            poste_id = request.POST.get('poste')
            
            # Création de l'utilisateur
            user = User.objects.create(
                email=email,
                matricule=matricule,
                nom=nom,
                prenom=prenom,
                poste_id=poste_id,
                statut='actif'  # Définir le statut comme actif
            )
            
            # Définition du mot de passe par défaut à "1234"
            default_password = "1234"
            user.set_password(default_password)
            user.save()
            
            messages.success(request, f"L'utilisateur {user.prenom} {user.nom} a été créé avec succès. Mot de passe par défaut: 1234")
            return redirect('users')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de l'utilisateur : {str(e)}")
            return redirect('users')
    
    return redirect('users')

@login_required
@user_passes_test(is_admin_or_chef)
def user_delete(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        try:
            # Libérer le poste occupé avant suppression
            if user.poste:
                user.poste.est_occupe = False
                user.poste.save()
            user.delete()
            messages.success(request, f"L'utilisateur {user.prenom} {user.nom} a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de l'utilisateur : {str(e)}")
    return redirect('users')



@login_required
@user_passes_test(is_admin_or_chef)
def users_list(request):
    # Récupération des paramètres de filtrage
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    structure_filter = request.GET.get('structure', '')
    status_filter = request.GET.get('status', '')
    
    # Query de base
    users = User.objects.all()
    
    # Application des filtres
    if search_query:
        users = users.filter(
            Q(prenom__icontains=search_query) |
            Q(nom__icontains=search_query) |
            Q(matricule__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if role_filter:
        if role_filter == 'agent':
            users = users.filter(poste__est_chef=False, est_admin=False)
        elif role_filter == 'chef':
            users = users.filter(poste__est_chef=True)
        elif role_filter == 'admin':
            users = users.filter(est_admin=True)
    
    if structure_filter:
        users = users.filter(poste__service__direction_id=structure_filter)
    
    if status_filter:
        users = users.filter(statut=status_filter)
    
    # Pagination
    paginator = Paginator(users, 10)  # 10 utilisateurs par page
    page = request.GET.get('page')
    users_page = paginator.get_page(page)
    
    # Ajouter le formulaire au contexte
    form = UserRegistrationForm()
    context = {
        'users': users_page,
        'structures': Direction.objects.all(),
        'search_query': search_query,
        'role_filter': role_filter,
        'structure_filter': structure_filter,
        'status_filter': status_filter,
        'form': form,  # Ajout du formulaire
    }
    
    return render(request, 'users.html', context)

@login_required
def dashboard(request):
    # Statistiques générales
    archive_count = Folder.objects.filter(est_supprime=False).count() + Piece.objects.filter(est_supprime=False).count()
    folder_count = Folder.objects.filter(est_supprime=False).count()
    piece_count = Piece.objects.filter(est_supprime=False).count()
    trash_count = TrashItem.objects.count()
    public_count = Folder.objects.filter(est_public=True, est_supprime=False).count() + Piece.objects.filter(est_public=True, est_supprime=False).count()
    private_count = Folder.objects.filter(est_public=False, est_supprime=False).count() + Piece.objects.filter(est_public=False, est_supprime=False).count()

    # Activités récentes dossiers et pièces
    recent_folder_activities = FolderHistory.objects.select_related('utilisateur').order_by('-action_date')[:5]
    recent_piece_activities = PieceHistory.objects.select_related('utilisateur').order_by('-action_date')[:5]

    context = {
        'archive_count': archive_count,
        'folder_count': folder_count,
        'piece_count': piece_count,
        'trash_count': trash_count,
        'public_count': public_count,
        'private_count': private_count,
        'user_count': User.objects.filter(statut='actif').count(),
        'pending_archives_count': Folder.objects.filter(importance__in=['elevee', 'critique'], est_supprime=False).count(),
        'notification_count': 0,  # À implémenter selon votre logique de notifications

        # Activités récentes
        'recent_folder_activities': recent_folder_activities,
        'recent_piece_activities': recent_piece_activities,

        # Distribution par importance
        'importance_counts': [
            Folder.objects.filter(importance='faible', est_supprime=False).count() + Piece.objects.filter(importance='faible', est_supprime=False).count(),
            Folder.objects.filter(importance='moyenne', est_supprime=False).count() + Piece.objects.filter(importance='moyenne', est_supprime=False).count(),
            Folder.objects.filter(importance='elevee', est_supprime=False).count() + Piece.objects.filter(importance='elevee', est_supprime=False).count(),
            Folder.objects.filter(importance='critique', est_supprime=False).count() + Piece.objects.filter(importance='critique', est_supprime=False).count(),
        ],

        'current_date': timezone.now()
    }

    return render(request, 'dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data.get('identifier')
            password = form.cleaned_data.get('password')
            
            # Utiliser le même paramètre 'identifier' que dans le backend
            user = authenticate(request, identifier=identifier, password=password)
                
            if user is not None:
                if user.statut == StatutChoices.ACTIF:
                    login(request, user)
                    return redirect('dashboard')
                else:
                    messages.error(request, "Votre compte n'est pas encore activé ou a été désactivé.")
            else:
                messages.error(request, "Identifiants invalides. Veuillez réessayer.")
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Votre compte a été créé avec succès. Un administrateur va examiner votre demande.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def load_services(request):
    direction_id = request.GET.get('direction')
    services = Service.objects.filter(direction_id=direction_id)
    return JsonResponse(list(services.values('id', 'nom')), safe=False)

def load_postes(request):
    service_id = request.GET.get('service')
    postes = Poste.objects.filter(service_id=service_id, est_occupe=False)
    return JsonResponse(list(postes.values('id', 'nom')), safe=False)

def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')

@login_required
@user_passes_test(is_admin_or_chef)
def user_activate(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        try:
            user.statut = 'actif'
            user.save()
            
            # Créer un historique de validation
            ValidationHistory.objects.create(
                demande=user,
                valide_par=request.user,
                statut='actif',
                commentaire=f"Compte validé par {request.user.get_full_name()}",
                date_demande=user.date_inscription,
                date_validation=timezone.now()
            )
            
            messages.success(request, f"Le compte de {user.prenom} {user.nom} a été activé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'activation du compte : {str(e)}")
    
    return redirect('users')

@login_required
def profile_view(request):
    return render(request, 'profiles.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, "Le mot de passe actuel est incorrect.")
            return redirect('profile')
        elif new_password != confirm_password:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            return redirect('profile')
        elif len(new_password) < 8:
            messages.error(request, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
            return redirect('profile')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
            
            # Mise à jour de la session pour éviter la déconnexion
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            return redirect('profile')
            
    return redirect('profile')

@login_required
@user_passes_test(lambda u: u.est_admin)
def archive_types(request):
    folder_types = FolderType.objects.all()
    piece_types = PieceType.objects.filter(type_dossier__isnull=True)
    context = {
        'folder_types': folder_types,
        'piece_types': piece_types
    }
    return render(request, 'archive_types.html', context)



@login_required
def add_type(request, folder_type_id=None):
    folder_type = None
    if folder_type_id:
        folder_type = get_object_or_404(FolderType, id=folder_type_id)
        


    if request.method == 'POST':
        try:
            type_categorie = request.POST.get('typeCategorie')
            nom = request.POST.get('nom').strip()
            description = request.POST.get('description', '').strip()

            if not nom:
                messages.error(request, 'Le nom est requis.')
                return render(request, 'add_type.html', {
                    'folder_type': folder_type
                })
                
            if type_categorie == 'piece' and folder_type:
                piece_type = PieceType.objects.create(
                    nom=nom,
                    description=description,
                    type_dossier=folder_type,
                    createur=request.user
                )

            elif type_categorie == 'folder':
                FolderType.objects.create(
                    nom=nom,
                    description=description,
                    createur=request.user
                )
            elif type_categorie == 'piece':
                piece_type = PieceType.objects.create(
                    nom=nom,
                    description=description,
                    type_dossier=folder_type,
                    createur=request.user
                )

            messages.success(request, f'Type de {type_categorie} créé avec succès')
            return redirect('archive_types')

        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')

    return render(request, 'add_type.html', {
        'folder_type': folder_type
    })

@login_required
@user_passes_test(lambda u: u.est_admin)
def type_delete(request, type_id, category):
    if request.method == 'POST':
        try:
            if category == 'folder':
                obj = get_object_or_404(FolderType, id=type_id)
            else:
                obj = get_object_or_404(PieceType, id=type_id)
            
            obj.delete()
            messages.success(request, "Type supprimé avec succès")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
    
    return redirect('archive_types')
   

@login_required
def get_piece_types(request, folder_type_id):
    piece_types = PieceType.objects.filter(type_dossier_id=folder_type_id)
    data = [{
        'id': str(pt.id),
        'nom': pt.nom,
        'description': pt.description
    } for pt in piece_types]
    return JsonResponse(data, safe=False)

@login_required
def edit_type_view(request, type_id):
    category = request.GET.get('category', request.POST.get('category'))
    
    if category not in ['folder', 'piece']:
        messages.error(request, "Catégorie invalide")
        return redirect('archive_types')

    TypeModel = FolderType if category == 'folder' else PieceType
    type_obj = get_object_or_404(TypeModel, id=type_id)

    if request.method == "POST":
        try:
            nom = request.POST.get('nom', '').strip()
            description = request.POST.get('description', '').strip()

            if not nom:
                messages.error(request, 'Le nom est requis.')
                return render(request, 'edit_type.html', {
                    'type_obj': type_obj,
                    'category': category
                })

            type_obj.nom = nom
            type_obj.description = description
            type_obj.save()
            messages.success(request, 'Type modifié avec succès')
            return redirect('archive_types')

        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {str(e)}")

    return render(request, 'edit_type.html', {
        'type_obj': type_obj,
        'category': category
    })
    
    
    
@login_required
def add_archive(request):
    context = {
        'directions': Direction.objects.all(),
        'folder_types': FolderType.objects.all(),
        'piece_types': PieceType.objects.all(),
        'importance_choices': ImportanceChoices.choices,
        'keywords': Keyword.objects.all().order_by('nom'),
    }
    



    
    return render(request, 'add_archive.html', context)



@login_required
def add_archive_folder(request):
    context = {
        'directions': Direction.objects.all(),
        'folder_types': FolderType.objects.all(),
        'piece_types': PieceType.objects.all(),
        'importance_choices': ImportanceChoices.choices,
        'keywords': Keyword.objects.all().order_by('nom'),
    }

    if request.method == 'POST':
        try:
            folder = Folder.objects.create(
                titre=request.POST.get('titre'),
                description=request.POST.get('description'),
                createur=request.user,
                direction_id=request.POST.get('structure'),
                dossier_parent_id=request.POST.get('type_dossier'),
                provenance=request.POST.get('provenance'),
                importance=request.POST.get('importance'),
                dossier_date=request.POST.get('date'),
                est_public=request.POST.get('est_public') == 'on'
            )

            # Ajout des mots-clés au dossier
            mots_cles = request.POST.get('mots_cles', '').split(',')
            for mot in mots_cles:
                mot_clean = mot.strip().lower()
                if mot_clean:
                    keyword, _ = Keyword.objects.get_or_create(nom=mot_clean)
                    FolderKeyword.objects.create(folder=folder, keyword=keyword)

            # Correction ici : compter les fichiers dans request.FILES
            piece_indexes = []
            for key in request.FILES:
                match = re.match(r'pieces\[(\d+)\]\[fichier\]', key)
                if match:
                    piece_indexes.append(int(match.group(1)))
            piece_indexes.sort()
            piece_count = len(piece_indexes)

            for i in piece_indexes:
                file_field = f'pieces[{i}][fichier]'
                if file_field in request.FILES:
                    fichier = request.FILES[file_field]
                           # Lire le contenu du fichier
                    file_data = fichier.read()
                    # Chiffrer le contenu
                    encrypted_data = encrypt_file(file_data)
                    # Créer un fichier en mémoire pour Django
                    from django.core.files.base import ContentFile
                    encrypted_file = ContentFile(encrypted_data, name=fichier.name)
                    # Enregistrer la pièce avec le fichier chiffré
                    piece = Piece.objects.create(
                        titre=request.POST.get(f'pieces[{i}][titre]'),
                        numero=request.POST.get(f'pieces[{i}][numero]'),
                        description=request.POST.get(f'pieces[{i}][description]', ''),
                        fichier=encrypted_file,
                        fichier_taille=len(encrypted_data),
                        piece_date=request.POST.get(f'pieces[{i}][date_piece]'),
                        createur=request.user,
                        entite=folder.direction.nom,
                        type_id=request.POST.get(f'pieces[{i}][type]'),
                        duree_vie=request.POST.get(f'pieces[{i}][duree_vie]'),
                        est_public=folder.est_public,
                        dossier=folder,
                        importance=folder.importance
                    )

                    # Ajouter les mêmes mots-clés que le dossier
                    for keyword in folder.keyword.all():
                        PieceKeyword.objects.create(piece=piece, keyword=keyword)

                    PieceHistory.objects.create(
                        piece=piece,
                        utilisateur=request.user,
                        action_type=ActionTypeChoices.CREATION,
                        details=f"Création de la pièce dans le dossier {folder.titre}"
                    )

            FolderHistory.objects.create(
                dossier=folder,
                utilisateur=request.user,
                action_type=ActionTypeChoices.CREATION,
                details=f"Création du dossier avec {piece_count} pièces"
            )

            messages.success(request, f"Dossier créé avec succès avec {piece_count} pièces")
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {str(e)}")

    return render(request, 'add_archive_folder.html', context)




@login_required
def add_archive_secretariat(request):
    context = {
        'directions': Direction.objects.all(),
        'piece_types': PieceType.objects.all(),
        'importance_choices': ImportanceChoices.choices,
        'keywords': Keyword.objects.all().order_by('nom'),
    }

    if request.method == 'POST':
        try:
            piece_indexes = []
            for key in request.FILES:
                match = re.match(r'pieces\[(\d+)\]\[fichier\]', key)
                if match:
                    piece_indexes.append(int(match.group(1)))
            piece_indexes.sort()
            piece_count = len(piece_indexes)
                        
            for i in piece_indexes:
                file_field = f'pieces[{i}][fichier]'
                if file_field in request.FILES:
                    fichier = request.FILES[file_field]
                    file_data = fichier.read()
                    encrypted_data = encrypt_file(file_data)
                    from django.core.files.base import ContentFile
                    encrypted_file = ContentFile(encrypted_data, name=fichier.name)
                    piece = Piece.objects.create(
                        titre=request.POST.get(f'pieces[{i}][titre]'),
                        numero=request.POST.get(f'pieces[{i}][numero]'),
                        description=request.POST.get(f'pieces[{i}][description]', ''),
                        fichier=encrypted_file,
                        fichier_taille=len(encrypted_data),
                        piece_date=request.POST.get('date'),
                        createur=request.user,
                        entite=Direction.objects.get(id=request.POST.get('structure')).nom,
                        type_id=request.POST.get(f'pieces[{i}][type]'),
                        duree_vie=request.POST.get(f'pieces[{i}][duree_vie]'),
                        est_public=request.POST.get('est_public') == 'on',
                        dossier=None,
                        importance=request.POST.get('importance')
                    )

                    mots_cles = request.POST.get('mots_cles', '').split(',')
                    mots_cles = request.POST.get('mots_cles', '').split(',')
                    for mot in mots_cles:
                        mot_clean = mot.strip().lower()
                        if mot_clean:
                            keyword, _ = Keyword.objects.get_or_create(nom=mot_clean)
                            PieceKeyword.objects.create(piece=piece, keyword=keyword)

                    PieceHistory.objects.create(
                        piece=piece,
                        utilisateur=request.user,
                        action_type=ActionTypeChoices.CREATION,
                        details="Création de la pièce (secrétariat)"
                    )

            messages.success(request, f"{piece_count} pièce(s) créée(s) avec succès")
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {str(e)}")

    return render(request, 'add_archive_secretariat.html', context)


@login_required
def get_piece_types_for_folder(request, folder_type_id):
    try:
        piece_types = PieceType.objects.filter(type_dossier_id=folder_type_id).values('id', 'nom')
        return JsonResponse(list(piece_types), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

@login_required
def archives_list(request):
    user = request.user

    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    structure_filter = request.GET.get('structure', '')
    importance_filter = request.GET.get('importance', '')

    user_poste = getattr(user, 'poste', None)
    user_service = getattr(user_poste, 'service', None) if user_poste else None
    user_direction = getattr(user_service, 'direction', None) if user_service else None

    if user.est_admin or (user_poste and user_poste.est_chef):
        folders = Folder.objects.filter(est_supprime=False)
        pieces = Piece.objects.filter(est_supprime=False, dossier__isnull=True)  # <-- SEULEMENT les pièces sans dossier
    else:
        folder_q = Q(est_public=True)
        piece_q = Q(est_public=True)
        if user_poste:
            folder_q |= Q(folderpermission__beneficiaire=user_poste, folderpermission__peut_lire=True)
            piece_q |= Q(piecepermission__beneficiaire=user_poste, piecepermission__peut_lire=True)
        if user_direction:
            folder_q |= Q(folderpermission__direction_beneficiaire=user_direction, folderpermission__peut_lire=True)
            piece_q |= Q(piecepermission__direction_beneficiaire=user_direction, piecepermission__peut_lire=True)
        if user_service:
            folder_q |= Q(folderpermission__structure_beneficiaire=user_service, folderpermission__peut_lire=True)
            piece_q |= Q(piecepermission__structure_beneficiaire=user_service, piecepermission__peut_lire=True)

        folders = Folder.objects.filter(folder_q, est_supprime=False).distinct()
        pieces = Piece.objects.filter(piece_q, est_supprime=False, dossier__isnull=True).distinct()  # <-- SEULEMENT les pièces sans dossier

    if search_query:
        folders = folders.filter(titre__icontains=search_query)
        pieces = pieces.filter(titre__icontains=search_query)

    if type_filter:
        if type_filter.startswith('folder_'):
            folder_type_id = type_filter.replace('folder_', '')
            folders = folders.filter(dossier_parent_id=folder_type_id)
            pieces = pieces.none()
        elif type_filter.startswith('piece_'):
            piece_type_id = type_filter.replace('piece_', '')
            pieces = pieces.filter(type_id=piece_type_id)
            folders = folders.none()
        else:
            folders = folders.filter(dossier_parent_id=type_filter)
            pieces = pieces.filter(type_id=type_filter)

    if structure_filter:
        folders = folders.filter(direction_id=structure_filter)
        pieces = pieces.filter(entite__icontains=structure_filter)

    if importance_filter:
        folders = folders.filter(importance=importance_filter)
        pieces = pieces.filter(importance=importance_filter)

    # Calcul des droits pour le template
    for folder in folders:
        folder.can_edit = (
            user.est_admin or
            (user_poste and user_poste.est_chef) or
            folder.folderpermission_set.filter(beneficiaire=user_poste, peut_editer=True).exists() or
            (user_direction and folder.folderpermission_set.filter(direction_beneficiaire=user_direction, peut_editer=True).exists()) or
            (user_service and folder.folderpermission_set.filter(structure_beneficiaire=user_service, peut_editer=True).exists())
        )
        folder.can_delete = (
            user.est_admin or
            (user_poste and user_poste.est_chef) or
            folder.folderpermission_set.filter(beneficiaire=user_poste, peut_supprime=True).exists() or
            (user_direction and folder.folderpermission_set.filter(direction_beneficiaire=user_direction, peut_supprime=True).exists()) or
            (user_service and folder.folderpermission_set.filter(structure_beneficiaire=user_service, peut_supprime=True).exists())
        )
        folder.can_perm = (
            user.est_admin or
            (user_poste and user_poste.est_chef) or
            folder.createur_id == user.id
        )

    for piece in pieces:
        piece.can_edit = (
            user.est_admin or
            (user_poste and user_poste.est_chef) or
            piece.piecepermission_set.filter(beneficiaire=user_poste, peut_editer=True).exists() or
            (user_direction and piece.piecepermission_set.filter(direction_beneficiaire=user_direction, peut_editer=True).exists()) or
            (user_service and piece.piecepermission_set.filter(structure_beneficiaire=user_service, peut_editer=True).exists())
        )
        piece.can_delete = (
            user.est_admin or
            (user_poste and user_poste.est_chef) or
            piece.piecepermission_set.filter(beneficiaire=user_poste, peut_supprime=True).exists() or
            (user_direction and piece.piecepermission_set.filter(direction_beneficiaire=user_direction, peut_supprime=True).exists()) or
            (user_service and piece.piecepermission_set.filter(structure_beneficiaire=user_service, peut_supprime=True).exists())
        )
        piece.can_perm = (
            user.est_admin or
            (user_poste and user_poste.est_chef) or
            piece.createur_id == user.id
        )
        
    # Fusionne les deux QuerySets en une seule liste ordonnée par date décroissante
    all_items = list(folders) + list(pieces)
    all_items.sort(key=lambda obj: getattr(obj, 'dossier_date', getattr(obj, 'piece_date', None)), reverse=True)

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(all_items, 12)  # 12 éléments par page
    page_obj = paginator.get_page(page_number)

    context = {
        'folders': folders,
        'pieces': pieces,
        'structures': Direction.objects.all(),
        'folder_types': FolderType.objects.all(),
        'piece_types': PieceType.objects.all(),
        'importance_choices': ImportanceChoices.choices,
        'search_query': search_query,
        'type_filter': type_filter,
        'structure_filter': structure_filter,
        'importance_filter': importance_filter,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'archives_list.html', context)


@login_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    pieces = folder.pieces.all()
    # Historique de consultation
    FolderHistory.objects.create(
        dossier=folder,
        utilisateur=request.user,
        action_type=ActionTypeChoices.CONSULTATION,
        details="Consultation du dossier"
    )
    # Récupérer l'historique du dossier (modifications, suppressions, consultations, etc.)
    history = folder.folderhistory_set.select_related('utilisateur').order_by('-action_date')
    context = {
        'folder': folder,
        'pieces': pieces,
        'history': history,
    }
    return render(request, 'folder_detail.html', context)


@login_required
def view_piece(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    # Historique de consultation
    PieceHistory.objects.create(
        piece=piece,
        utilisateur=request.user,
        action_type=ActionTypeChoices.CONSULTATION,
        details="Consultation de la pièce"
    )
    encrypted_data = piece.fichier.read()
    decrypted_data = decrypt_file(encrypted_data)
    response = HttpResponse(decrypted_data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{piece.fichier.name}"'
    return response


@login_required
def edit_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    user = request.user
    if not (user.est_admin or (user.poste and user.poste.est_chef) or folder.folderpermission_set.filter(beneficiaire=user, peut_editer=True).exists()):
        messages.error(request, "Vous n'avez pas la permission de modifier ce dossier.")
        return redirect('archives')

    importance_choices = ImportanceChoices.choices

    if request.method == 'POST':
        folder.titre = request.POST.get('titre', folder.titre)
        folder.description = request.POST.get('description', folder.description)
        folder.importance = request.POST.get('importance', folder.importance)
        folder.est_public = request.POST.get('est_public') == 'on'
        folder.save()
        # Historique de modification
        FolderHistory.objects.create(
            dossier=folder,
            utilisateur=user,
            action_type=ActionTypeChoices.MODIFICATION,
            details="Modification du dossier"
        )
        messages.success(request, "Dossier modifié avec succès.")
        return redirect('archives')
    return render(request, 'edit_folder.html', {'folder': folder, 'importance_choices': importance_choices})


@login_required
def edit_piece(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    user = request.user
    # Vérification des permissions
    if not (user.est_admin or (user.poste and user.poste.est_chef) or piece.piecepermission_set.filter(beneficiaire=user, peut_editer=True).exists()):
        messages.error(request, "Vous n'avez pas la permission de modifier ce document.")
        return redirect('archives')

    if request.method == 'POST':
        form = PieceForm(request.POST, request.FILES, instance=piece)
        if form.is_valid():
            form.save()
             # Historique de modification
            PieceHistory.objects.create(
                piece=piece,
                utilisateur=user,
                action_type=ActionTypeChoices.MODIFICATION,
                details="Modification de la pièce"
            )
            messages.success(request, "Document modifié avec succès.")
            return redirect('archives')
    else:
        form = PieceForm(instance=piece)
    return render(request, 'edit_piece.html', {'form': form, 'piece': piece})


@login_required
def delete_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    user = request.user
    if not (user.est_admin or (user.poste and user.poste.est_chef) or folder.folderpermission_set.filter(beneficiaire=user, peut_supprime=True).exists()):
        messages.error(request, "Vous n'avez pas la permission de supprimer ce dossier.")
        return redirect('archives')

    if request.method == 'POST':
        justification = request.POST.get('justification', '').strip()
        if len(justification) < 20:
            messages.error(request, "La justification doit contenir au moins 20 caractères.")
            return render(request, 'delete_folder.html', {'folder': folder})

        TrashItem.objects.create(
            item_type='dossier',
            dossier=folder,
            supprime_par=user,
            justification=justification
        )
        for piece in folder.pieces.all():
            TrashItem.objects.create(
                item_type='piece',
                piece=piece,
                dossier=folder,
                supprime_par=user,
                justification=f"Suppression liée au dossier : {justification}"
            )
            piece.est_supprime = True
            piece.save()
            # Historique suppression pièce
            PieceHistory.objects.create(
                piece=piece,
                utilisateur=user,
                action_type=ActionTypeChoices.SUPPRESSION,
                details=f"Suppression de la pièce liée au dossier : {justification}"
            )
        folder.est_supprime = True
        folder.save()
        # Historique suppression dossier
        FolderHistory.objects.create(
            dossier=folder,
            utilisateur=user,
            action_type=ActionTypeChoices.SUPPRESSION,
            details=f"Suppression du dossier : {justification}"
        )
        messages.success(request, "Dossier et ses pièces supprimés avec succès.")
        return redirect('archives')
    return render(request, 'delete_folder.html', {'folder': folder})

@login_required
def delete_piece(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    user = request.user
    if not (user.est_admin or (user.poste and user.poste.est_chef) or piece.piecepermission_set.filter(beneficiaire=user, peut_supprime=True).exists()):
        messages.error(request, "Vous n'avez pas la permission de supprimer ce document.")
        return redirect('archives')

    if request.method == 'POST':
        justification = request.POST.get('justification', '').strip()
        if len(justification) < 20:
            messages.error(request, "La justification doit contenir au moins 20 caractères.")
            return render(request, 'delete_piece.html', {'piece': piece})

        TrashItem.objects.create(
            item_type='piece',
            piece=piece,
            dossier=piece.dossier,
            supprime_par=user,
            justification=justification
        )
        piece.est_supprime = True
        piece.save()
        # Historique suppression pièce
        PieceHistory.objects.create(
            piece=piece,
            utilisateur=user,
            action_type=ActionTypeChoices.SUPPRESSION,
            details=f"Suppression de la pièce : {justification}"
        )
        messages.success(request, "Document supprimé avec succès.")
        return redirect('archives')
    return render(request, 'delete_piece.html', {'piece': piece})
@login_required
def folder_permissions(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    user = request.user
    if not (user.est_admin or (user.poste and user.poste.est_chef) or folder.createur_id == user.id):
        messages.error(request, "Vous n'avez pas la permission de gérer les droits sur ce dossier.")
        return redirect('archives')

    if request.method == 'POST':
        # Suppression d'une permission
        permission_id = request.POST.get('permission_a_supprimer')
        if permission_id:
            perm = FolderPermission.objects.filter(id=permission_id, dossier=folder).first()
            if perm:
                perm.delete()
                messages.success(request, "Permission supprimée avec succès.")
            else:
                messages.error(request, "Permission introuvable.")
        else:
            # Ajout de permissions (logique existante)
            beneficiaires_ids = request.POST.getlist('beneficiaires')
            directions_ids = request.POST.getlist('directions')
            services_ids = request.POST.getlist('services')
            peut_lire = bool(request.POST.get('peut_lire'))
            peut_editer = bool(request.POST.get('peut_editer'))
            peut_supprime = bool(request.POST.get('peut_supprime'))

            count = 0

            for poste_id in beneficiaires_ids:
                poste = Poste.objects.filter(id=poste_id).first()
                if poste:
                    FolderPermission.objects.create(
                        dossier=folder,
                        beneficiaire=poste,
                        peut_lire=peut_lire,
                        peut_editer=peut_editer,
                        peut_supprime=peut_supprime,
                        donneur=user
                    )
                    count += 1

            for direction_id in directions_ids:
                direction = Direction.objects.filter(id=direction_id).first()
                if direction:
                    FolderPermission.objects.create(
                        dossier=folder,
                        direction_beneficiaire=direction,
                        peut_lire=peut_lire,
                        peut_editer=peut_editer,
                        peut_supprime=peut_supprime,
                        donneur=user
                    )
                    count += 1

            for service_id in services_ids:
                service = Service.objects.filter(id=service_id).first()
                if service:
                    FolderPermission.objects.create(
                        dossier=folder,
                        structure_beneficiaire=service,
                        peut_lire=peut_lire,
                        peut_editer=peut_editer,
                        peut_supprime=peut_supprime,
                        donneur=user
                    )
                    count += 1

            if count == 0:
                messages.error(request, "Veuillez sélectionner au moins un poste, une direction ou un service.")
            else:
                messages.success(request, f"{count} permission(s) ajoutée(s) avec succès.")

    permissions = FolderPermission.objects.filter(dossier=folder)
    postes = Poste.objects.all()
    directions = Direction.objects.all()
    services = Service.objects.all()
    return render(request, 'permissions_folder.html', {
        'folder': folder,
        'permissions': permissions,
        'postes': postes,
        'directions': directions,
        'services': services,
    })

@login_required
def piece_permissions(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    user = request.user
    if not (user.est_admin or (user.poste and user.poste.est_chef) or piece.createur_id == user.id):
        messages.error(request, "Vous n'avez pas la permission de gérer les droits sur ce document.")
        return redirect('archives')

    if request.method == 'POST':
        # Suppression d'une permission
        permission_id = request.POST.get('permission_a_supprimer')
        if permission_id:
            perm = PiecePermission.objects.filter(id=permission_id, piece=piece).first()
            if perm:
                perm.delete()
                messages.success(request, "Permission supprimée avec succès.")
            else:
                messages.error(request, "Permission introuvable.")
        else:
            # Ajout de permissions (logique existante)
            beneficiaires_ids = request.POST.getlist('beneficiaires')
            directions_ids = request.POST.getlist('directions')
            services_ids = request.POST.getlist('services')
            peut_lire = bool(request.POST.get('peut_lire'))
            peut_editer = bool(request.POST.get('peut_editer'))
            peut_supprime = bool(request.POST.get('peut_supprime'))

            count = 0

            for poste_id in beneficiaires_ids:
                poste = Poste.objects.filter(id=poste_id).first()
                if poste:
                    PiecePermission.objects.create(
                        piece=piece,
                        beneficiaire=poste,
                        peut_lire=peut_lire,
                        peut_editer=peut_editer,
                        peut_supprime=peut_supprime,
                        donneur=user
                    )
                    count += 1

            for direction_id in directions_ids:
                direction = Direction.objects.filter(id=direction_id).first()
                if direction:
                    PiecePermission.objects.create(
                        piece=piece,
                        direction_beneficiaire=direction,
                        peut_lire=peut_lire,
                        peut_editer=peut_editer,
                        peut_supprime=peut_supprime,
                        donneur=user
                    )
                    count += 1

            for service_id in services_ids:
                service = Service.objects.filter(id=service_id).first()
                if service:
                    PiecePermission.objects.create(
                        piece=piece,
                        structure_beneficiaire=service,
                        peut_lire=peut_lire,
                        peut_editer=peut_editer,
                        peut_supprime=peut_supprime,
                        donneur=user
                    )
                    count += 1

            if count == 0:
                messages.error(request, "Veuillez sélectionner au moins un poste, une direction ou un service.")
            else:
                messages.success(request, f"{count} permission(s) ajoutée(s) avec succès.")

    permissions = PiecePermission.objects.filter(piece=piece)
    postes = Poste.objects.all()
    directions = Direction.objects.all()
    services = Service.objects.all()
    return render(request, 'permissions_piece.html', {
        'piece': piece,
        'permissions': permissions,
        'postes': postes,
        'directions': directions,
        'services': services,
    })


@login_required
@user_passes_test(is_admin_or_chef)
def organisation(request):
    directions = Direction.objects.all()
    services = Service.objects.all()
    postes = Poste.objects.all()
    return render(request, 'organisation.html', {
        'directions': directions,
        'services': services,
        'postes': postes,
    })

# --- Directions ---
@login_required
@user_passes_test(is_admin_or_chef)
def add_direction(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description', '')
        if nom:
            Direction.objects.create(nom=nom, description=description)
            messages.success(request, "Direction ajoutée avec succès.")
            return redirect('organisation')
        messages.error(request, "Le nom est obligatoire.")
    return render(request, 'add_edit_direction.html')

@login_required
@user_passes_test(is_admin_or_chef)
def edit_direction(request, direction_id):
    direction = get_object_or_404(Direction, id=direction_id)
    if request.method == 'POST':
        direction.nom = request.POST.get('nom')
        direction.description = request.POST.get('description', '')
        direction.save()
        messages.success(request, "Direction modifiée avec succès.")
        return redirect('organisation')
    return render(request, 'add_edit_direction.html', {'direction': direction})

@login_required
@user_passes_test(is_admin_or_chef)
def delete_direction(request, direction_id):
    direction = get_object_or_404(Direction, id=direction_id)
    if request.method == 'POST':
        direction.delete()
        messages.success(request, "Direction supprimée avec succès.")
        return redirect('organisation')
    return render(request, 'delete_direction.html', {'direction': direction})

# --- Services ---
@login_required
@user_passes_test(is_admin_or_chef)
def add_service(request):
    directions = Direction.objects.all()
    if request.method == 'POST':
        nom = request.POST.get('nom')
        direction_id = request.POST.get('direction')
        description = request.POST.get('description', '')
        if nom and direction_id:
            Service.objects.create(nom=nom, direction_id=direction_id, description=description)
            messages.success(request, "Service ajouté avec succès.")
            return redirect('organisation')
        messages.error(request, "Le nom et la direction sont obligatoires.")
    return render(request, 'add_edit_service.html', {'directions': directions})

@login_required
@user_passes_test(is_admin_or_chef)
def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    directions = Direction.objects.all()
    if request.method == 'POST':
        service.nom = request.POST.get('nom')
        service.direction_id = request.POST.get('direction')
        service.description = request.POST.get('description', '')
        service.save()
        messages.success(request, "Service modifié avec succès.")
        return redirect('organisation')
    return render(request, 'add_edit_service.html', {'service': service, 'directions': directions})

@login_required
@user_passes_test(is_admin_or_chef)
def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Service supprimé avec succès.")
        return redirect('organisation')
    return render(request, 'delete_service.html', {'service': service})

# --- Postes ---
@login_required
@user_passes_test(is_admin_or_chef)
def add_poste(request):
    services = Service.objects.all()
    if request.method == 'POST':
        nom = request.POST.get('nom')
        service_id = request.POST.get('service')
        description = request.POST.get('description', '')
        est_chef = bool(request.POST.get('est_chef'))
        est_occupe = bool(request.POST.get('est_occupe'))
        if nom and service_id:
            Poste.objects.create(
                nom=nom,
                service_id=service_id,
                description=description,
                est_chef=est_chef,
                est_occupe=est_occupe
            )
            messages.success(request, "Poste ajouté avec succès.")
            return redirect('organisation')
        messages.error(request, "Le nom et le service sont obligatoires.")
    return render(request, 'add_edit_poste.html', {'services': services})

@login_required
@user_passes_test(is_admin_or_chef)
def edit_poste(request, poste_id):
    poste = get_object_or_404(Poste, id=poste_id)
    services = Service.objects.all()
    if request.method == 'POST':
        poste.nom = request.POST.get('nom')
        poste.service_id = request.POST.get('service')
        poste.description = request.POST.get('description', '')
        poste.est_chef = bool(request.POST.get('est_chef'))
        poste.est_occupe = bool(request.POST.get('est_occupe'))
        poste.save()
        messages.success(request, "Poste modifié avec succès.")
        return redirect('organisation')
    return render(request, 'add_edit_poste.html', {'poste': poste, 'services': services})

@login_required
@user_passes_test(is_admin_or_chef)
def delete_poste(request, poste_id):
    poste = get_object_or_404(Poste, id=poste_id)
    if request.method == 'POST':
        poste.delete()
        messages.success(request, "Poste supprimé avec succès.")
        return redirect('organisation')
    return render(request, 'delete_poste.html', {'poste': poste})


@login_required
def trash(request):
    search_query = request.GET.get('search', '')
    structure_filter = request.GET.get('structure', '')
    importance_filter = request.GET.get('importance', '')
    public_only = request.GET.get('public_only', '') == 'on'

    trash_items = TrashItem.objects.select_related('dossier', 'piece', 'supprime_par')

    # Filtres
    if search_query:
        trash_items = trash_items.filter(
            Q(dossier__titre__icontains=search_query) |
            Q(piece__titre__icontains=search_query) |
            Q(supprime_par__prenom__icontains=search_query) |
            Q(supprime_par__nom__icontains=search_query)
        )
    if structure_filter:
        trash_items = trash_items.filter(
            Q(dossier__direction_id=structure_filter) |
            Q(piece__entite__icontains=structure_filter)
        )
    if importance_filter:
        trash_items = trash_items.filter(
            Q(dossier__importance=importance_filter) |
            Q(piece__importance=importance_filter)
        )
    if public_only:
        trash_items = trash_items.filter(
            Q(dossier__est_public=True) | Q(piece__est_public=True)
        )

    structures = Direction.objects.all()
    importance_choices = ImportanceChoices.choices

    context = {
        'trash_items': trash_items.order_by('-date_suppression'),
        'structures': structures,
        'importance_choices': importance_choices,
        'search_query': search_query,
        'structure_filter': structure_filter,
        'importance_filter': importance_filter,
        'public_only': public_only,
    }
    return render(request, 'trash.html', context)


from django.utils import timezone

@login_required
def restore_trash_item(request, item_id):
    item = get_object_or_404(TrashItem, id=item_id)
    if request.method == 'POST':
        # Restaurer le dossier ou la pièce
        if item.dossier:
            item.dossier.est_supprime = False
            item.dossier.save()
            # Restaurer aussi toutes les pièces du dossier si c'est un dossier
            for piece in item.dossier.pieces.all():
                piece.est_supprime = False
                piece.save()
        if item.piece:
            item.piece.est_supprime = False
            item.piece.save()
        # Supprimer l'entrée de corbeille
        item.delete()
        messages.success(request, "Élément restauré avec succès.")
    return redirect('trash')

@login_required
def delete_trash_item(request, item_id):
    item = get_object_or_404(TrashItem, id=item_id)
    if request.method == 'POST':
        # Si l'archive n'est pas restaurée, supprimer aussi l'objet et le média
        if not getattr(item, 'est_restauré', False):
            if item.piece:
                # Supprimer le fichier média si présent
                if item.piece.fichier and item.piece.fichier.name:
                    item.piece.fichier.delete(save=False)
                item.piece.delete()
            elif item.dossier:
                # Supprimer toutes les pièces liées et leurs fichiers
                for piece in item.dossier.pieces.all():
                    if piece.fichier and piece.fichier.name:
                        piece.fichier.delete(save=False)
                    piece.delete()
                item.dossier.delete()
        # Supprimer l'entrée de corbeille
        item.delete()
        messages.success(request, "Élément supprimé définitivement.")
    return redirect('trash')


@login_required
def piece_detail(request, piece_id):
    try:
        piece = Piece.objects.get(id=piece_id, est_supprime=False)
    except Piece.DoesNotExist:
        return render(request, "piece_detail.html", {"piece": None})

    # Enregistrer l'action de consultation
    PieceHistory.objects.create(
        piece=piece,
        utilisateur=request.user,
        action_type=ActionTypeChoices.CONSULTATION,
        details="Consultation de la fiche détail"
    )

    similar_pieces = Piece.objects.filter(est_supprime=False).exclude(id=piece.id)
    if piece.dossier and piece.dossier.direction:
        similar_pieces = similar_pieces.filter(dossier__direction=piece.dossier.direction)
    elif piece.entite:
        similar_pieces = similar_pieces.filter(entite=piece.entite)
    similar_pieces = similar_pieces[:3]

    abs_url = None
    if piece.fichier:
        abs_url = request.build_absolute_uri(piece.fichier.url)

    history = piece.piecehistory_set.select_related('utilisateur').order_by('-action_date')

    return render(request, "piece_detail.html", {
        "piece": piece,
        "similar_pieces": similar_pieces,
        "abs_url": abs_url,
        "history": history,
    })

from django.http import FileResponse
from django.contrib.auth.decorators import login_required

@login_required
def piece_file_view(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    # Vérifie les permissions ici si besoin
    return FileResponse(piece.fichier, as_attachment=False)

from django.http import FileResponse, Http404
from core.utils.crypto import decrypt_file
from io import BytesIO

@login_required
def piece_preview(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    # Vérifie les droits d'accès ici si besoin

    # Lis le fichier chiffré
    piece.fichier.open('rb')
    encrypted_data = piece.fichier.read()
    piece.fichier.close()
    try:
        decrypted_data = decrypt_file(encrypted_data)
    except Exception:
        raise Http404("Erreur de déchiffrement")

    # Déduire le content_type
    filename = piece.fichier.name.lower()
    if filename.endswith('.pdf'):
        content_type = 'application/pdf'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif filename.endswith('.png'):
        content_type = 'image/png'
    elif filename.endswith('.gif'):
        content_type = 'image/gif'
    elif filename.endswith('.doc') or filename.endswith('.docx'):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif filename.endswith('.xls') or filename.endswith('.xlsx'):
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename.endswith('.ppt') or filename.endswith('.pptx'):
        content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    else:
        content_type = 'application/octet-stream'

    return FileResponse(BytesIO(decrypted_data), content_type=content_type)