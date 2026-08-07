from django.db import IntegrityError
from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Review

from .serializers import CreateReviewSerializer, ReviewSerializer


class ReviewListCreateView(APIView):
    """
    GET  /api/reviews/?product_id=X  — list reviews for a product + average rating (public)
    POST /api/reviews/               — submit a review (logged-in customers only)

    One review per user per product — the `review` table already has a
    unique(user_id, product_id) constraint, so a second attempt comes
    back as a clean 409 instead of a raw database error.
    """
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return []

    def get(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"error": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        reviews = (
            Review.objects.filter(product_id=product_id)
            .select_related('user')
            .order_by('-created_at')
        )
        average = reviews.aggregate(avg=Avg('rating'))['avg']

        return Response({
            "product_id": int(product_id),
            "count": reviews.count(),
            "average_rating": round(average, 2) if average is not None else None,
            "results": ReviewSerializer(reviews, many=True).data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.get_product()
        data = serializer.validated_data

        try:
            review = Review.objects.create(
                user=request.user,
                product=product,
                rating=data['rating'],
                comment=data['comment'],
                created_at=timezone.now(),
                is_verified_purchase=0,  # not wired to order history yet — see README
            )
        except IntegrityError:
            return Response(
                {"error": "You've already reviewed this product."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
