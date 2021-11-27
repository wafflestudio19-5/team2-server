from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.views import Response, APIView
import os

# Create your views here.

class PingPongView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        return Response(data={'ping': 'pong'}, status=status.HTTP_200_OK)

