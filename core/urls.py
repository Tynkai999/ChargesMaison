from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    path("periodes/", views.period_list, name="period_list"),
    path("periodes/ajouter/", views.period_add, name="period_add"),
    path("periodes/<uuid:pk>/modifier/", views.period_edit, name="period_edit"),
    path("periodes/<uuid:pk>/", views.period_detail, name="period_detail"),
    path("periodes/<uuid:pk>/supprimer/", views.period_delete, name="period_delete"),
    path("periodes/<uuid:pk>/charges/ajouter/", views.charge_add, name="charge_add"),
    path("periodes/<uuid:pk>/charges/<uuid:charge_id>/modifier/", views.charge_edit, name="charge_edit"),
    path("periodes/<uuid:pk>/charges/<uuid:charge_id>/supprimer/", views.charge_delete, name="charge_delete"),
    path("periodes/<uuid:pk>/presences/", views.presence_update, name="presence_update"),
    path("periodes/<uuid:pk>/wifi/ajouter/", views.wifi_contribution_add, name="wifi_contribution_add"),
    path("periodes/<uuid:pk>/wifi/<uuid:wc_id>/modifier/", views.wifi_contribution_edit, name="wifi_contribution_edit"),
    path("periodes/<uuid:pk>/wifi/<uuid:wc_id>/supprimer/", views.wifi_contribution_delete, name="wifi_contribution_delete"),

    path("periodes/<uuid:pk>/pdf/", views.period_pdf_all, name="period_pdf_all"),
    path("periodes/<uuid:pk>/pdf/<uuid:resident_id>/", views.contribution_pdf, name="contribution_pdf"),
    path("periodes/<uuid:pk>/pdf/<uuid:resident_id>/envoyer/", views.contribution_pdf_send, name="contribution_pdf_send"),
    path("periodes/<uuid:pk>/paiements/", views.payment_tracking, name="payment_tracking"),

    path("contributeurs/", views.contributor_list, name="contributor_list"),
    path("contributeurs/<uuid:pk>/modifier/", views.contributor_edit, name="contributor_edit"),
    path("contributeurs/<uuid:pk>/supprimer/", views.contributor_delete, name="contributor_delete"),

    path("types-de-charge/", views.charge_type_list, name="charge_type_list"),
    path("types-de-charge/<uuid:pk>/modifier/", views.charge_type_edit, name="charge_type_edit"),
    path("types-de-charge/<uuid:pk>/supprimer/", views.charge_type_delete, name="charge_type_delete"),

    path("residents/", views.resident_list, name="resident_list"),
    path("residents/ajouter/", views.resident_add, name="resident_add"),
    path("residents/<uuid:pk>/modifier/", views.resident_edit, name="resident_edit"),

    path("mes-contributions/", views.my_contributions, name="my_contributions"),
]
