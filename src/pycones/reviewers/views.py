from braces.views import GroupRequiredMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from options.models import Option

from pycones.reviewers import REVIEW_GROUP_NAME
from pycones.reviewers.forms import ReviewForm, ReviewerSignUpForm, ReviewsFilterForm
from pycones.reviewers.helpers import create_reviews
from pycones.reviewers.models import Review


class BaseReviewerView(GroupRequiredMixin, View):
    group_required = REVIEW_GROUP_NAME
    login_url = reverse_lazy("users:sign-in")


class ReviewListView(BaseReviewerView):
    template_name = "reviewers/list.html"

    def get(self, request):
        create_reviews(request.user)
        reviews = Review.objects.filter(user=request.user)
        activate_reviews = Option.objects.get_value("activate_reviews", 0)
        if not request.user.is_superuser and not activate_reviews:
            reviews = Review.objects.none()
        filter_form = ReviewsFilterForm(request.GET)
        if filter_form.is_valid() and filter_form.cleaned_data["only_unfinished"]:
            reviews = reviews.filter(finished=False)
        data = {"reviews": reviews, "filter_form": filter_form}
        return render(request, self.template_name, data)


class ReviewView(BaseReviewerView):
    template_name = "reviewers/details.html"

    def get(self, request, pk):
        if request.user.is_superuser:
            review = get_object_or_404(Review, pk=pk)
        else:
            review = get_object_or_404(Review, pk=pk, user=request.user)
        form = ReviewForm(instance=review)
        data = {"review": review, "proposal": review.proposal, "form": form}
        return render(request, self.template_name, data)

    def post(self, request, pk):
        if request.user.is_superuser:
            review = get_object_or_404(Review, pk=pk)
        else:
            review = get_object_or_404(Review, pk=pk, user=request.user)
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect(reverse("reviewers:details", kwargs={"pk": review.pk}))
        data = {"review": review, "proposal": review.proposal, "form": form}
        return render(request, self.template_name, data)


class ReviewerSignUpView(View):
    """View to register a reviewer."""

    template_name = "reviewers/sign_up.html"

    def get(self, request):
        form = ReviewerSignUpForm()
        data = {"form": form}
        return render(request, self.template_name, data)

    def post(self, request):
        form = ReviewerSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("reviewers:sign-up-success"))
        data = {"form": form}
        return render(request, self.template_name, data)
