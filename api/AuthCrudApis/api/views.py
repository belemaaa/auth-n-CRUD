from django.shortcuts import render
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from .models import Post
from .serializers import PostSerializer, UserLoginSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import User


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key})
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class PostView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, pk=None, *args, **kwargs):
        if pk is not None:
            object = get_object_or_404(Post, pk=pk)
            data = PostSerializer(object, many=False).data
            return Response(data)

        queryset = Post.objects.all()
        data = PostSerializer(queryset, many=True).data
        return Response(data)

    def post(self, request, *args, **kwargs):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            title = serializer.validated_data.get('title')
            content = serializer.validated_data.get('content') or None
            if content is None:
                content = title
            serializer.save(user=self.request.user, content=content)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
    
    def get_object(self, pk):
        return get_object_or_404(Post, pk=pk)
    
    def put(self, request, pk=None, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = PostSerializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        instance = self.get_object(pk)
        instance.delete()

        return Response({'message': 'Resource deleted successfully'}, status=204)
    
class GetUserPosts(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, *args, **kwargs):
        queryset = Post.objects.filter(user=request.user)
        data = PostSerializer(queryset, many=True).data
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "posts": data
        })

