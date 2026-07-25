from django.contrib import admin
from django.contrib.admin import AdminSite


class XYZAdminSite(AdminSite):
    site_header = 'XYZ Boshqaruv paneli'
    site_title = 'XYZ Admin'
    index_title = 'Platformani nazorat qilish'
    site_url = '/'


# Keep for reference; project uses default admin.site with branding in apps.core.apps.
admin_site = XYZAdminSite(name='xyz_admin')
