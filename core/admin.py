from django.contrib import admin
from .models import Usuario, Categoria, Marca, Producto, Oferta, Direccion, Carrito, CarritoItem, Pedido, PedidoItem, Pago
from django.contrib.auth.admin import UserAdmin

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    model = Usuario
    list_display = ('username','email','is_staff','is_active')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('telefono','direccion','ciudad')}),
    )


admin.site.register(Categoria)
admin.site.register(Marca)
admin.site.register(Producto)
admin.site.register(Oferta)
admin.site.register(Direccion)
admin.site.register(Carrito)
admin.site.register(CarritoItem)
admin.site.register(Pedido)
admin.site.register(PedidoItem)
admin.site.register(Pago)
