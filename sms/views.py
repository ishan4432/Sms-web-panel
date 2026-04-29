from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import Message

@api_view(['GET'])
@renderer_classes([JSONRenderer])
def test_api(request):
    return Response({"message": "API working 🚀"})


@api_view(['POST'])
@renderer_classes([JSONRenderer])
def send_sms(request):
    phone = request.data.get('phone')
    message = request.data.get('message')

    Message.objects.create(
        phone_number=phone,
        content=message
    )

    return Response({"status": "Message stored"})
