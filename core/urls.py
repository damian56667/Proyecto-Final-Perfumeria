from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.inicio, name="inicio"),

    # PRODUCTOS
    path("tienda/", views.perfumes, name="tienda"),
    path("producto/<int:pk>/", views.producto_detail, name="producto_detail"),
    path("categoria/<slug:slug>/", views.productos_por_categoria, name="productos_categoria"),

    # OFERTAS
    path("ofertas/", views.ofertas_public, name="ofertas"),
    path("oferta/agregar-carrito/<int:oferta_id>/", views.agregar_oferta_carrito, name="agregar_oferta_carrito"),

    # PAGINAS
    path("perfumes/", views.perfumes, name="perfumes"),
    path("marcas/", views.marcas_public, name="marcas"),
    path("contacto/", views.contacto, name="contacto"),

    # AUTH
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.registro, name="registro"),

    # CARRITO
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/agregar/<int:producto_id>/", views.agregar_carrito, name="agregar_carrito"),
    path("carrito/eliminar/<int:item_id>/", views.eliminar_carrito, name="eliminar_carrito"),
    path("carrito/cambiar/<int:item_id>/", views.cambiar_cantidad, name="cambiar_cantidad"),
    path("carrito/reparar/", views.reparar_precios_carrito, name="reparar_precios"),

    # CHECKOUT
    path("checkout/", views.checkout, name="checkout"),
    path("confirmacion-pedido/<int:pedido_id>/", views.confirmacion_pedido, name="confirmacion_pedido"),

    # ADMIN
    path("panel/", views.admin_dashboard, name="admin_dashboard"),
    path("panel/productos/", views.admin_productos, name="admin_productos"),
    path("panel/producto/nuevo/", views.admin_producto_agregar, name="admin_producto_agregar"),
    path("panel/producto/editar/<int:id>/", views.admin_producto_editar, name="admin_producto_editar"),
    path("panel/producto/eliminar/<int:id>/", views.admin_producto_eliminar, name="admin_producto_eliminar"),

    path("panel/categorias/", views.admin_categorias, name="admin_categorias"),
    path("panel/categoria/nueva/", views.admin_categoria_agregar, name="admin_categoria_agregar"),
    path("panel/categoria/editar/<int:id>/", views.admin_categoria_editar, name="admin_categoria_editar"),
    path("panel/categoria/eliminar/<int:id>/", views.admin_categoria_eliminar, name="admin_categoria_eliminar"),

    path("panel/marcas/", views.admin_marcas, name="admin_marcas"),
    path("panel/marca/nueva/", views.admin_marca_agregar, name="admin_marca_agregar"),
    path("panel/marca/editar/<int:id>/", views.admin_marca_editar, name="admin_marca_editar"),
    path("panel/marca/eliminar/<int:id>/", views.admin_marca_eliminar, name="admin_marca_eliminar"),

    path("panel/ofertas/", views.admin_ofertas, name="admin_ofertas"),
    path("panel/oferta/nueva/", views.admin_oferta_agregar, name="admin_oferta_agregar"),
    path("panel/oferta/editar/<int:id>/", views.admin_oferta_editar, name="admin_oferta_editar"),
    path("panel/oferta/eliminar/<int:id>/", views.admin_oferta_eliminar, name="admin_oferta_eliminar"),

    path("panel/usuarios/", views.admin_usuarios, name="admin_usuarios"),
    path("panel/usuario/eliminar/<int:id>/", views.admin_usuario_eliminar, name="admin_usuario_eliminar"),

    path("panel/pedidos/", views.admin_pedidos, name="admin_pedidos"),
    path("panel/pedido/<int:id>/", views.admin_pedido_detalle, name="admin_pedido_detalle"),
    path("panel/pedidos/eliminar/<int:id>/", views.admin_pedido_eliminar, name="admin_pedido_eliminar"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
