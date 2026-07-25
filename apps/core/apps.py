from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Sayt kontenti'

    def ready(self):
        from django.contrib import admin
        from django.contrib.auth.models import Group

        admin.site.site_header = 'XYZ Boshqaruv'
        admin.site.site_title = 'XYZ Admin'
        admin.site.index_title = 'Boshqaruv paneli'
        admin.site.site_url = '/'

        # Oddiy adminlar uchun Groups chalkash — yashiramiz
        try:
            admin.site.unregister(Group)
        except admin.sites.NotRegistered:
            pass
