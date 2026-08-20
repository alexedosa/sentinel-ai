from intelio.models import UserSignal


def save_user_signal(request):
    return UserSignal.objects.create(
        request=request
    )
