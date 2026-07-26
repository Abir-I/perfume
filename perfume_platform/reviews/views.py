from django.db import IntegrityError
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import OrderItem, Review

from .serializers import CreateReviewSerializer, ReviewSerializer


class ReviewListCreateView(APIView):
    """
    GET  /api/reviews/?product_id=X - all reviews for a product, plus the
         average rating. Public - no login required to browse reviews.
    POST /api/reviews/               - submit a review for a product.
         Requires login. One review per (user, product) - the DB has a
         UNIQUE(user_id, product_id) constraint, enforced here as a clean
         400 instead of a raw IntegrityError.
    """
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return []

    def get(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {"error": "product_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product_id = int(product_id)
        except ValueError:
            return Response(
                {"error": "product_id must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reviews = Review.objects.select_related('user').filter(
            product_id=product_id
        ).order_by('-created_at')

        stats = reviews.aggregate(average_rating=Avg('rating'), review_count=Count('review_id'))
        average_rating = stats['average_rating']

        return Response({
            "product_id": product_id,
            "average_rating": round(average_rating, 2) if average_rating is not None else None,
            "review_count": stats['review_count'],
            "reviews": ReviewSerializer(reviews, many=True).data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.get_product()
        rating = serializer.validated_data['rating']
        comment = serializer.validated_data.get('comment', '')

        # a review is "verified purchase" if the reviewer has actually
        # bought this product in a past order
        already_purchased = OrderItem.objects.filter(
            order__user=request.user, product=product,
        ).exists()

        try:
            review = Review.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                comment=comment,
                created_at=timezone.now(),
                is_verified_purchase=1 if already_purchased else 0,
            )
        except IntegrityError:
            return Response(
                {"error": "You've already reviewed this product."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
