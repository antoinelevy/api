from datetime import datetime, timedelta
import logging
from uuid import uuid4

from django.conf import settings
from drf_pdf.renderer import PDFRenderer
import jwt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from wkhtmltopdf import views as wkhtmltopdf_views

from cel import serializers
from cyclos_api import CyclosAPI, CyclosAPIException
from dolibarr_api import DolibarrAPI, DolibarrAPIException
from members.misc import Member
from misc import sendmail_euskalmoneta


log = logging.getLogger()


@api_view(['POST'])
@permission_classes((AllowAny, ))
def first_connection(request):
    """
    First connection
    """
    serializer = serializers.FirstConnectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)

    try:
        dolibarr = DolibarrAPI()
        dolibarr_token = dolibarr.login(login=settings.DOLIBARR_ANONYMOUS_LOGIN,
                                        password=settings.DOLIBARR_ANONYMOUS_PASSWORD)

        valid_login = Member.validate_num_adherent(request.data['login'])

        if valid_login:
            # We want to search in members by login (N° Adhérent)
            try:
                response = dolibarr.get(model='members', login=request.data['login'], api_key=dolibarr_token)
            except DolibarrAPIException:
                return Response(status=status.HTTP_204_NO_CONTENT)

            if response[0]['email'] == request.data['email']:
                # We got a match!

                # We need to mail a token etc...
                payload = {'login': request.data['login'],
                           'aud': 'member', 'iss': 'first-connection',
                           'jti': str(uuid4()), 'iat': datetime.utcnow(),
                           'nbf': datetime.utcnow(), 'exp': datetime.utcnow() + timedelta(hours=1)}

                jwt_token = jwt.encode(payload, settings.JWT_SECRET)
                confirm_url = '{}/valide-premiere-connexion?token={}'.format(settings.CEL_PUBLIC_URL,
                                                                             jwt_token.decode("utf-8"))

                sendmail_euskalmoneta(subject="subject", body="body blabla, token: {}".format(confirm_url),
                                      to_email=request.data['email'])
                return Response({'member': 'OK'})
            else:
                return Response({'member': None})

        else:
            return Response({'error': 'You need to provide a *VALID* login parameter! (Format: E12345)'},
                            status=status.HTTP_400_BAD_REQUEST)

    except DolibarrAPIException:
        return Response({'error': 'Unable to connect to Dolibarr!'}, status=status.HTTP_400_BAD_REQUEST)
    except (KeyError, IndexError):
        return Response({'error': 'Unable to get user ID from your username!'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def validate_first_connection(request):
    """
    validate_first_connection
    """
    serializer = serializers.ValidTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)

    try:
        token_data = jwt.decode(request.data['token'], settings.JWT_SECRET,
                                issuer='first-connection', audience='member')
    except jwt.InvalidTokenError as e:
        return Response({'error': 'Unable to read token!'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(token_data)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def lost_password(request):
    """
    User login from dolibarr
    """
    serializer = serializers.LostPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)

    try:
        pass
        # dolibarr = DolibarrAPI()
        # request.data['login']
        # request.data['email']
    except DolibarrAPIException:
        return Response({'error': 'Unable to connect to Dolibarr!'}, status=status.HTTP_400_BAD_REQUEST)
    except (KeyError, IndexError):
        return Response({'error': 'Unable to get user ID from your username!'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def validate_lost_password(request):
    """
    validate_lost_password
    """
    pass


@api_view(['GET'])
def account_summary_for_adherents(request):

    try:
        cyclos = CyclosAPI(auth_string=request.user.profile.cyclos_auth_string, mode='cel')
    except CyclosAPIException:
        return Response({'error': 'Unable to connect to Cyclos!'}, status=status.HTTP_400_BAD_REQUEST)

    query_data = [cyclos.user_id, None]

    accounts_summaries_data = cyclos.post(method='account/getAccountsSummary', data=query_data)
    return Response(accounts_summaries_data)


@api_view(['GET'])
def payments_available_for_adherents(request):

    serializer = serializers.HistorySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    try:
        cyclos = CyclosAPI(auth_string=request.user.profile.cyclos_auth_string, mode='cel')
    except CyclosAPIException:
        return Response({'error': 'Unable to connect to Cyclos!'}, status=status.HTTP_400_BAD_REQUEST)

    query_data = [cyclos.user_id, None]

    accounts_summaries_data = cyclos.post(method='account/getAccountsSummary', data=query_data)
    begin_date = datetime.strptime(request.query_params['begin'], '%Y-%m-%d')
    end_date = datetime.strptime(
        request.query_params['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    search_history_data = {
        'account': accounts_summaries_data['result'][0]['status']['accountId'],
        'orderBy': 'DATE_DESC',
        'pageSize': 1000,  # maximum pageSize: 1000
        'currentpage': 0,
        'period':
        {
            'begin': begin_date.isoformat(),
            'end': end_date.isoformat(),
        },
    }

    accounts_history_res = cyclos.post(method='account/searchAccountHistory', data=search_history_data)
    return Response(accounts_history_res)


@api_view(['GET'])
@renderer_classes((PDFRenderer, ))
def export_history_adherent_pdf(request):

    serializer = serializers.HistorySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    try:
        cyclos = CyclosAPI(auth_string=request.user.profile.cyclos_auth_string, mode='cel')
    except CyclosAPIException:
        return Response({'error': 'Unable to connect to Cyclos!'}, status=status.HTTP_400_BAD_REQUEST)

    query_data = [cyclos.user_id, None]

    accounts_summaries_data = cyclos.post(method='account/getAccountsSummary', data=query_data)
    begin_date = request.query_params['begin']
    end_date = request.query_params['end']

    search_history_data = {
        'account': accounts_summaries_data['result'][0]['status']['accountId'],
        'orderBy': 'DATE_DESC',
        'pageSize': 1000,  # maximum pageSize: 1000
        'currentpage': 0,
        'period':
        {
            'begin': begin_date,
            'end': end_date,
        },
    }
    accounts_history_res = cyclos.post(method='account/searchAccountHistory', data=search_history_data)
    context = {
        'account_history': accounts_history_res['result'],
    }

    response = wkhtmltopdf_views.PDFTemplateResponse(request=request, context=context, template="summary/summary.html")
    pdf_content = response.rendered_content

    headers = {
        'Content-Disposition': 'filename="pdf_id.pdf"',
        'Content-Length': len(pdf_content),
    }

    return Response(pdf_content, headers=headers)
