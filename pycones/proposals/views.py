# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from options.models import Option

from pycones.blog.models import Post
from pycones.proposals.forms import ProposalFrom, EditProposalFrom
from pycones.proposals.models import Proposal


def get_more_info_link():
    try:
        post_pk = Option.objects.get_value("submit_proposal_post_pk", 2)
        more_info_link = Post.objects.get(pk=post_pk).get_absolute_url()
    except Post.DoesNotExist:
        return ""
    return more_info_link


class SubmitProposalView(View):
    """View to submit proposals."""

    @staticmethod
    def get(request):
        is_submit_proposal_opened = bool(
            Option.objects.get_value("submit_proposal_opened", 1)
        )
        if (
            is_submit_proposal_opened
            or request.user.is_authenticated
            and request.user.is_staff
        ):
            form = ProposalFrom()
            data = {"form": form, "more_info_link": get_more_info_link()}
            return render(request, "proposals/create.html", data)
        return render(request, "proposals/close.html")

    @staticmethod
    def post(request):
        is_submit_proposal_opened = bool(
            Option.objects.get_value("submit_proposal_opened", 1)
        )
        if not (
            is_submit_proposal_opened
            or request.user.is_authenticated
            and request.user.is_staff
        ):
            return render(request, "proposals/close.html")
        form = ProposalFrom(request.POST)
        data = {"form": form, "more_info_link": get_more_info_link()}
        if form.is_valid():
            form.save()
            return redirect("proposals:success")
        return render(request, "proposals/create.html", data)


class EditProposalView(View):
    """View to edit proposals."""

    form = EditProposalFrom

    @staticmethod
    def serialize_speakers(speakers):
        return json.dumps(
            [{"name": speaker.name, "email": speaker.email} for speaker in speakers]
        )

    def get(self, request, code):
        proposal = get_object_or_404(Proposal, code=code)
        edit_proposals_allowed = bool(
            Option.objects.get_value("edit_proposals_allowed", 1)
        )
        if edit_proposals_allowed:
            form = self.form(
                instance=proposal,
                initial={
                    "speakers": self.serialize_speakers(
                        proposal.speakers.order_by("created")
                    )
                },
            )
            data = {"form": form, "more_info_link": get_more_info_link()}
            return render(request, "proposals/edit.html", data)
        return render(request, "proposals/close.html")

    def post(self, request, code):
        proposal = get_object_or_404(Proposal, code=code)
        edit_proposals_allowed = bool(
            Option.objects.get_value("edit_proposals_allowed", 1)
        )
        if not edit_proposals_allowed:
            return render(request, "proposals/close.html")
        form = self.form(request.POST, instance=proposal)
        data = {"form": form, "more_info_link": get_more_info_link()}
        if form.is_valid():
            form.save()
            return redirect(reverse("proposals:edit", kwargs={"code": code}))
        return render(request, "proposals/edit.html", data)
