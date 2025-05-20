from django.contrib import admin
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('ajax/load-services/', views.load_services, name='ajax_load_services'),
    path('ajax/load-postes/', views.load_postes, name='ajax_load_postes'),
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.users_list, name='users'),
    path('utilisateurs/', views.users_list, name='users'),
    path('utilisateurs/creer/', views.user_create, name='user_create'),
    path('utilisateurs/<str:user_id>/supprimer/', views.user_delete, name='user_delete'),
    path('utilisateurs/<str:user_id>/activer/', views.user_activate, name='user_activate'),
    path('utilisateurs/<str:user_id>/desactiver/', views.user_deactivate, name='user_deactivate'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('types/', views.archive_types, name='archive_types'),
    path('types/add/', views.add_type, name='add_type'),
    path('types/add/<uuid:folder_type_id>/piece/', views.add_type, name='add_piece_type'), 
    path('types/<uuid:type_id>/<str:category>/delete/', views.type_delete, name='type_delete'),
    path('types/<uuid:type_id>/edit/', views.edit_type_view, name='edit_type'),
    path('types/<uuid:folder_type_id>/pieces/', views.get_piece_types, name='get_piece_types'),
    path('archives/', views.archives_list, name='archives'),
    path('archives/add/', views.add_archive, name='add_archive'),
    path('archives/folder/add/', views.add_archive_folder, name='add_archive_folder'),
    path('archives/secretariat/add/', views.add_archive_secretariat, name='add_archive_secretariat'),
    path('piece-types/<uuid:folder_type_id>/', views.get_piece_types_for_folder, name='get_piece_types_for_folder'),
    path('archives/folder/<uuid:folder_id>/', views.folder_detail, name='folder_detail'),
    path('pieces/<uuid:piece_id>/download/', views.view_piece, name='download_piece'),
    path('archives/folder/<uuid:folder_id>/edit/', views.edit_folder, name='edit_folder'),
    path('archives/folder/<uuid:folder_id>/delete/', views.delete_folder, name='delete_folder'),
    path('pieces/<uuid:piece_id>/edit/', views.edit_piece, name='edit_piece'),
    path('pieces/<uuid:piece_id>/delete/', views.delete_piece, name='delete_piece'),
    path('archives/folder/<uuid:folder_id>/permissions/', views.folder_permissions, name='folder_permissions'),
    path('pieces/<uuid:piece_id>/permissions/', views.piece_permissions, name='piece_permissions'),
    # ...
    path('organisation/', views.organisation, name='organisation'),

    # Directions
    path('organisation/direction/add/', views.add_direction, name='add_direction'),
    path('organisation/direction/<uuid:direction_id>/edit/', views.edit_direction, name='edit_direction'),
    path('organisation/direction/<uuid:direction_id>/delete/', views.delete_direction, name='delete_direction'),

    # Services
    path('organisation/service/add/', views.add_service, name='add_service'),
    path('organisation/service/<uuid:service_id>/edit/', views.edit_service, name='edit_service'),
    path('organisation/service/<uuid:service_id>/delete/', views.delete_service, name='delete_service'),

    # Postes
    path('organisation/poste/add/', views.add_poste, name='add_poste'),
    path('organisation/poste/<uuid:poste_id>/edit/', views.edit_poste, name='edit_poste'),
    path('organisation/poste/<uuid:poste_id>/delete/', views.delete_poste, name='delete_poste'), 
    path('trash/', views.trash, name='trash'),
    
    path('trash/', views.trash, name='trash'),
    path('trash/<uuid:item_id>/restore/', views.restore_trash_item, name='restore_trash_item'),
    path('trash/<uuid:item_id>/delete/', views.delete_trash_item, name='delete_trash_item'),
    
    path('pieces/<uuid:piece_id>/view/', views.piece_detail, name='view_piece'),

    path('pieces/<uuid:piece_id>/file/', views.piece_file_view, name='piece_file_view'),
    path('pieces/<uuid:piece_id>/preview/', views.piece_preview, name='piece_preview'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
