from dj_rest_auth.serializers import PasswordResetSerializer
from django.conf import settings

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        """ Force custom template for password reset email """
        email_name = "password_reset"
        base_path = f"emails/{email_name}/{email_name}"
        
        return {
            "subject_template_name": f"{base_path}_subject.txt",
            "email_template_name": f"{base_path}_message.txt",
            "html_email_template_name": f"{base_path}_email.html",
            "extra_email_context": {
                "WEB_APP_URL": settings.WEB_APP_URL
            }
        }
