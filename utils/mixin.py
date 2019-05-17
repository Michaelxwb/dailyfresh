from django.contrib.auth.decorators import login_required


class LoginRequireMixin(object):
    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        view = login_required(view)
        return view
