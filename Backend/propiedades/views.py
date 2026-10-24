from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Propiedad, Favorito, Turno
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from .serializers import PropiedadSerializer, FavoritoSerializer, TurnoSerializer
from usuarios.permissions import ReadOnlyOrAdminGestor


class PropiedadViewSet(viewsets.ModelViewSet):
    queryset = Propiedad.objects.all().order_by("titulo")
    serializer_class = PropiedadSerializer
    ##permission_classes = [ReadOnlyOrAdminGestor]


@api_view(["GET"])
@permission_classes([AllowAny])
def propiedades_mobile(request):
    tipo = request.query_params.get("tipoOperacion")
    ciudad = request.query_params.get("ciudad")
    precio_max = request.query_params.get("precioMax")

    qs = Propiedad.objects.all().order_by("titulo")
    if tipo:
        qs = qs.filter(tipo_operacion__iexact=tipo)
    if ciudad:
        qs = qs.filter(ciudad__icontains=ciudad)
    if precio_max:
        try:
            qs = qs.filter(precio__lte=float(precio_max))
        except ValueError:
            pass

    data = [
        {
            "id": str(p.id_propiedad),
            "titulo": p.titulo,
            "tipoOperacion": p.tipo_operacion,
            "ciudad": p.ciudad,
            "precio": float(p.precio),
            "imagen": request.build_absolute_uri(p.imagen_1.url) if p.imagen_1 else None,
        }
        for p in qs
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def propiedad_detalle_mobile(request, id_propiedad):
    try:
        p = Propiedad.objects.get(id_propiedad=id_propiedad)
    except Propiedad.DoesNotExist:
        return Response({"error": "No encontrada"}, status=404)

    user = request.user
    if not user.is_authenticated:
        for authenticator in [TokenAuthentication(), JWTAuthentication()]:
            try:
                auth_result = authenticator.authenticate(request)
                if auth_result is not None:
                    user = auth_result[0]
                    break
            except Exception:
                pass

    es_favorito = False
    if request.user and request.user.is_authenticated:
        es_favorito = Favorito.objects.filter(usuario=request.user, propiedad=p).exists()

    imagenes = [
        request.build_absolute_uri(img.url)
        for img in (p.imagen_1, p.imagen_2, p.imagen_3)
        if img
    ]

    return Response({
        "id": str(p.id_propiedad),
        "titulo": p.titulo,
        "descripcion": p.descripcion,
        "tipoOperacion": p.tipo_operacion,
        "ciudad": p.ciudad,
        "precio": float(p.precio),
        "habitaciones": p.habitaciones,
        "banios": p.baños,
        "superficie": float(p.superficie),
        "aceptaMascotas": p.acepta_mascotas,
        "imagenes": imagenes,
        "esFavorito": es_favorito,
    })

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def favoritos_mobile(request):
    if request.method == "GET":
        favoritos = Favorito.objects.filter(usuario=request.user)
        serializer = FavoritoSerializer(favoritos, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == "POST":
        propiedad_id = request.data.get("id_propiedad") or request.data.get("propiedad")
        if not propiedad_id:
            return Response({"error": "Falta el campo id_propiedad"}, status=400)

        try:
            propiedad = Propiedad.objects.get(id_propiedad=propiedad_id)
        except Propiedad.DoesNotExist:
            return Response ({"error": "La propiedad no existe"}, status=404)

        favorito, creado = Favorito.objects.get_or_create(usuario=request.user, propiedad=propiedad)

        serializer = FavoritoSerializer(favorito, context={'request' : request})
        status_code = 201 if creado else 200
        return Response(serializer.data, status=status_code)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def eliminar_favorito_mobile(request, id_propiedad):
    try:
        favorito = Favorito.objects.get(usuario=request.user, propiedad_id=id_propiedad)
        favorito.delete()
        return Response ( status= 204)
    except Favorito.DoesNotExist:
        return Response({"error": "El favorito no existe"}, status=404)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def turnos_mobile(request):
    if request.method == "GET":
        turnos = Turno.objects.filter(usuario=request.user).order_by("fecha_hora")
        serializer = TurnoSerializer(turnos, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == "POST":
        propiedad_id = request.data.get("id_propiedad") or request.data.get("propiedad")
        fecha_hora_str = request.data.get("fecha_hora")

        if not propiedad_id or not fecha_hora_str:
            return Response({"error": "Faltan datos obligatorios (id_propiedad y fecha_hora)"}, status=400)

        try:
            propiedad = Propiedad.objects.get(id_propiedad=propiedad_id)
        except Propiedad.DoesNotExist:
            return Response({"error": "La propiedad no existe"}, status=404)

        fecha_parsed = parse_datetime(fecha_hora_str.replace(" ", "T"))
        if not fecha_parsed:
            return Response({"error": f"Formato de fecha inválido: {fecha_hora_str}"}, status=400)

        if timezone.is_naive(fecha_parsed):
            fecha_parsed = timezone.make_aware(fecha_parsed)

        try:
            turno = Turno.objects.create(
                usuario=request.user,
                propiedad=propiedad,
                fecha_hora=fecha_parsed
            )
            serializer = TurnoSerializer(turno, context={'request': request})
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({"error": f"Error interno en DB: {str(e)}"}, status=500)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancelar_turno_mobile(request, id_turno):
    try:
        turno = Turno.objects.get(id_turno=id_turno, usuario=request.user)
        turno.delete()
        return Response(status=204)
    except Turno.DoesNotExist:
        return Response({"error": "El turno no existe o no te pertenece"}, status=404)