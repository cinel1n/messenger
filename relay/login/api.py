from .serializers import *
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from .permissions import UserPermission
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()


class PeginatorAPIView(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserAPIView(APIView):
    pagination_class = PeginatorAPIView
    permission_classes = [UserPermission, ]

    #https://www.django-rest-framework.org/tutorial/3-class-based-views/#rewriting-our-api-using-class-based-views

    def get(self, request, pk=None):
        if pk is not None:
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(user)
        else:
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(
                User.objects.all(), 
                request, 
                view=self
            )
            serializer = UserSerializer(page, many=True)
            return paginator.get_paginated_response(
                serializer.data
            )

        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(
            user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

