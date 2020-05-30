from django.urls import reverse_lazy

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        return reverse_lazy('accounts:check_registration')
