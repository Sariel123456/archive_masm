from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from .models import *


class BaseModelAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        if request.user.is_staff or request.user.est_admin:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_staff or request.user.est_admin:
            return True
        return False

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if change:
                messages.success(request, "Modification effectuée avec succès.")
            else:
                messages.success(request, "Création effectuée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

@admin.register(User)
class UserAdmin(BaseModelAdmin):
    list_display = ('email', 'matricule', 'nom', 'prenom', 'statut', 'est_admin', 'is_staff')
    list_filter = ('statut', 'est_admin', 'is_staff')
    search_fields = ('email', 'matricule', 'nom', 'prenom')
    readonly_fields = ('date_inscription', 'derniere_connexion')

    def save_model(self, request, obj, form, change):
        try:
            # Vérification du poste avant la sauvegarde
            if obj.poste:
                # Si c'est une modification, récupérer l'ancien état
                if change:
                    old_obj = self.model.objects.get(pk=obj.pk)
                    old_poste = old_obj.poste
                    
                    # Si le poste a changé
                    if old_poste != obj.poste:
                        # Vérifier si le nouveau poste n'est pas déjà occupé
                        if obj.poste.est_occupe and User.objects.filter(poste=obj.poste).exists():
                            messages.error(request, "Ce poste est déjà occupé")
                            return
                            
                        # Libérer l'ancien poste
                        if old_poste:
                            old_poste.est_occupe = False
                            old_poste.save()
                            
                        # Marquer le nouveau poste comme occupé
                        obj.poste.est_occupe = True
                        obj.poste.save()

            # Assurer que les superusers sont actifs
            if obj.is_staff or obj.est_admin:
                obj.statut = 'actif'

            super().save_model(request, obj, form, change)
            
            if change:
                messages.success(request, "Modification effectuée avec succès.")
            else:
                messages.success(request, "Création effectuée avec succès.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la sauvegarde : {str(e)}")

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('email', 'matricule', 'nom', 'prenom', 'password')
        }),
        ('Affectation', {
            'fields': ('poste',)
        }),
        ('Statut et permissions', {
            'fields': ('statut', 'est_admin', 'is_staff')
        }),
        ('Dates', {
            'fields': ('date_inscription', 'derniere_connexion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom',)
    
    def save_model(self, request, obj, form, change):
        try:
            obj.save()
            if change:
                messages.success(request, "Direction modifiée avec succès.")
            else:
                messages.success(request, "Direction créée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la sauvegarde : {str(e)}")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'direction']
    list_filter = ['direction']
    search_fields = ['nom']

@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'service', 'est_occupe', 'est_chef')
    list_filter = ('service', 'est_occupe', 'est_chef')
    search_fields = ('nom',)


# Enregistrement des autres modèles avec le BaseModelAdmin
admin.site.register(ValidationHistory, BaseModelAdmin)
admin.site.register(FolderType, BaseModelAdmin)
admin.site.register(PieceType, BaseModelAdmin)
admin.site.register(Keyword, BaseModelAdmin)
admin.site.register(Folder, BaseModelAdmin)
admin.site.register(Piece, BaseModelAdmin)
admin.site.register(PieceHistory, BaseModelAdmin)
admin.site.register(FolderHistory, BaseModelAdmin)
admin.site.register(FolderPermission, BaseModelAdmin)
admin.site.register(PiecePermission, BaseModelAdmin)
admin.site.register(TrashItem, BaseModelAdmin)
admin.site.register(FolderKeyword, BaseModelAdmin)
admin.site.register(PieceKeyword, BaseModelAdmin)