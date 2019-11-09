# -*- coding: utf-8 -*-

import numpy as np
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


from pycones.utils.emails import send_email


class Review(TimeStampedModel):
    """A review assignation. A review user have assigned a proposal to
    review."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="reviews", on_delete=models.CASCADE
    )
    proposal = models.ForeignKey(
        "proposals.Proposal", related_name="reviews", on_delete=models.CASCADE
    )

    score = models.FloatField(
        verbose_name=_("Puntuación"),
        null=True,
        blank=True,
        help_text=_("Puntuación del 1.0 al 4.0"),
    )

    notes = models.TextField(verbose_name=_("Notas del revisor"), blank=True, null=True)

    conflict = models.BooleanField(
        verbose_name=_("¿Existe un conflicto de intereses?"), default=False
    )
    finished = models.BooleanField(
        verbose_name=_("¿Revisión finalizada?"), default=False
    )

    class Meta:
        unique_together = ["user", "proposal"]

    def notify(self):
        context = {
            "site": Site.objects.get_current(),
            "first_name": self.user.first_name,
            "title": self.proposal.title,
        }
        send_email(
            context=context,
            template="emails/reviewers/new.html",
            subject=_("[%s] Tienes una nueva propuesta para revisar")
            % settings.CONFERENCE_TITLE,
            to=self.user.email,
            from_email="%s <%s>" % (settings.CONFERENCE_TITLE, settings.CONTACT_EMAIL),
        )


class Reviewer(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="reviewer", on_delete=models.CASCADE
    )

    def reviews_count(self):
        return self.user.reviews.count()

    def num_reviews(self):
        return Review.objects.filter(user=self.user).count()

    def mean(self):
        values = [review.score or 0 for review in Review.objects.filter(user=self.user)]
        return np.mean(values)

    def std(self):
        values = [review.score or 0 for review in Review.objects.filter(user=self.user)]
        return np.std(values)
