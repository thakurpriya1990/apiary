import traceback
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from django_countries import countries
from rest_framework import viewsets, serializers, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from ledger_api_client.ledger_models import EmailUserRO as EmailUser,Address

from disturbance.components.users.serializers import (   
    UserSerializer,
    UserAddressSerializer,
    PersonalSerializer,
    ContactSerializer,
    MyUserDetailsSerializer,
)
from disturbance.helpers import is_internal

class GetCountries(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        country_list = []
        for country in list(countries):
            country_list.append({"name": country.name, "code": country.code})
        return Response(country_list)

class GetProfile(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        serializer  = UserSerializer(request.user,
                context={'request': request}
                )
        return Response(serializer.data)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailUser.objects.none()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return EmailUser.objects.all()
        elif user.is_authenticated:
            qs = EmailUser.objects.filter(Q(id=user.id))
            return qs
        return EmailUser.objects.none()

    #TODO on_cleanup may require adjustments
    #NOTE: technically should be internal only but effectively is via get_queryset
    @action(detail=False,methods=['GET',])
    def get_department_users(self, request, *args, **kwargs):
        try:
            search_term = request.GET.get('term', '')
            data = self.get_queryset().filter(
                is_staff=True).filter(
                    Q(first_name__icontains=search_term) | 
                    Q(last_name__icontains=search_term)
                ).values('email', 'first_name', 'last_name')[:10]
            data_transform = [{'id': person['email'], 'text': person['first_name'] + ' ' + person['last_name']} for person in data]
            return Response({"results": data_transform})
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['GET', ])
    def pending_org_requests(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = OrganisationRequestDTSerializer(
                instance.organisationrequest_set.filter(
                    status='with_assessor'),
                many=True,
                context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

class GetMyUserDetails(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        serializer = MyUserDetailsSerializer(request.user, context={'request': request})
        return Response(serializer.data)