from intelio.models import UserSignal


def save_user_signal(*, user, signal_text):
    """
    Persist a user-authored signal and explicitly associate it
    with the authenticated user.
    """

    return UserSignal.objects.create(
        user=user,
        request=signal_text,
    )
