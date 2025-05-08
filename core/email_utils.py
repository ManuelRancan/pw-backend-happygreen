# core/email_utils.py
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_verification_code(user):
    """Invia codice di verifica via email"""
    # Debug: stampa il codice nella console del server
    print(f"===============================================")
    print(f"CODICE DI VERIFICA per {user.email}: {user.verification_code}")
    print(f"===============================================")

    try:
        # Verifica che il template esista
        template_path = 'email/verification_code.html'

        html_message = render_to_string(
            template_path,
            {'user': user, 'code': user.verification_code}
        )

        # Versione testo
        plain_message = strip_tags(html_message)

        # Invia email
        send_mail(
            subject='HappyGreen - Verifica il tuo account',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Email inviata con successo a {user.email}")
        return True
    except Exception as e:
        print(f"Errore nell'invio dell'email: {str(e)}")
        # Solleva nuovamente l'eccezione per permettere alla vista di gestirla
        raise