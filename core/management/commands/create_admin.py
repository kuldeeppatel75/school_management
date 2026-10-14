
import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create the initial admin account if it does not exist"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Admin environment variables are missing."
                )
            )
            return

        user = User.objects.filter(username=username).first()

        if user:
            if not user.is_superuser or not user.is_staff:
                self.stdout.write(
                    self.style.ERROR(
                        f"{username} already exists but is not an admin. "
                        "No changes made."
                    )
                )
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin account '{username}' already exists."
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email="",
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin account '{username}' created successfully."
            )
        )
