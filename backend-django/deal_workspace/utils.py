from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model

from . import models

User = get_user_model()


def get_party_role_for_user(
    deal: models.Deal, user: User
) -> Optional[models.PartyRole]:
    if not user or not user.is_authenticated:
        return None
    return deal.party_roles.filter(user=user).first()


def user_is_admin(user: User) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_staff", False):
        return True
    return getattr(user, "role", None) == "admin"
