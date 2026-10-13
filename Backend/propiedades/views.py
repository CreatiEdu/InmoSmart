from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Propiedad
from .serializers import PropiedadSerializer
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
    })