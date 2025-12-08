from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import RegistroForm
from .models import (
    Producto, Marca, Categoria, Oferta,
    Carrito, CarritoItem, Usuario, Pedido,
)
from .forms import *
from django.utils import timezone
from decimal import Decimal
from .models import CarritoItem, PedidoItem
from .forms import RegistroForm
from django.contrib.auth.forms import AuthenticationForm
# -----------------------------Carrito, ItemCarrito
# DECORADORES PERSONALIZADOS
# -----------------------------
def es_staff(user):
    return user.is_authenticated and user.is_staff

# -----------------------------
# PÁGINAS PUBLICAS
# -----------------------------
# En tu función inicio() en views.py, actualízala así:
def inicio(request):
    # Obtener productos con stock
    productos = Producto.objects.filter(stock__gt=0).order_by('-creado')[:8]
    
    # Obtener ofertas ACTIVAS (que estén dentro de las fechas)
    hoy = timezone.now().date()
    ofertas_activas = Oferta.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    )[:3]
    
    # Obtener marcas para mostrar
    marcas = Marca.objects.all()[:6]
    
    # Obtener productos con ofertas para destacar
    productos_con_oferta = Producto.objects.filter(
        ofertas__fecha_inicio__lte=hoy,
        ofertas__fecha_fin__gte=hoy
    ).distinct()[:4]
    
    # Estadísticas
    total_productos = Producto.objects.filter(stock__gt=0).count()
    total_marcas = Marca.objects.count()
    
    return render(request, "core/inicio.html", {
        "productos": productos,
        "ofertas": ofertas_activas,
        "marcas": marcas,
        "productos_con_oferta": productos_con_oferta,
        "total_productos": total_productos,
        "total_marcas": total_marcas,
        "total_clientes": 1250,  # Puedes cambiar esto por datos reales
    })

def perfumes(request):
    productos = Producto.objects.filter(stock__gt=0)
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    
    # Aplicar filtros
    categoria_id = request.GET.get('categoria')
    marca_id = request.GET.get('marca')
    precio = request.GET.get('precio')
    stock = request.GET.get('stock')
    orden = request.GET.get('orden')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if marca_id:
        productos = productos.filter(marca_id=marca_id)
    
    if precio == 'menor-500':
        productos = productos.filter(precio__lt=500)
    elif precio == '500-1000':
        productos = productos.filter(precio__range=(500, 1000))
    elif precio == 'mayor-1000':
        productos = productos.filter(precio__gt=1000)
    
    if stock == 'agotado':
        productos = productos.filter(stock=0)
    elif stock == 'disponible':
        productos = productos.filter(stock__gt=0)
    
    # Ordenamiento
    if orden == 'precio-asc':
        productos = productos.order_by('precio')
    elif orden == 'precio-desc':
        productos = productos.order_by('-precio')
    elif orden == 'nombre-asc':
        productos = productos.order_by('nombre')
    else:
        productos = productos.order_by('-creado')  # Recientes por defecto
    
    return render(request, "core/perfumes.html", {
        "productos": productos,
        "categorias": categorias,
        "marcas": marcas,
    })

def productos_por_categoria(request, categoria_id=None):
    if categoria_id:
        productos = Producto.objects.filter(categoria_id=categoria_id, activo=True)
    else:
        productos = Producto.objects.filter(activo=True)
    
    categorias = Categoria.objects.all()
    
    return render(request, 'core/productos.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_id
    })

def marcas_public(request):
    marcas = Marca.objects.all()
    
    # Filtro por país
    pais = request.GET.get('pais')
    if pais:
        marcas = marcas.filter(pais_origen__icontains=pais)
    
    # Estadísticas
    paises = set(marca.pais_origen for marca in marcas if marca.pais_origen)
    total_productos = Producto.objects.filter(marca__in=marcas).count()
    marcas_con_logo = marcas.filter(imagen__isnull=False).count()
    
    return render(request, "core/marcas.html", {
        "marcas": marcas,
        "paises": sorted(paises),
        "paises_count": len(paises),
        "total_productos": total_productos,
        "marcas_con_logo": marcas_con_logo,
    })
# views.py - ACTUALIZADA
def ofertas_public(request):
    """
    Vista pública para mostrar ofertas con cálculos automáticos
    """
    hoy = timezone.now().date()
    
    try:
        # Intentar obtener ofertas de la base de datos
        ofertas_db = Oferta.objects.all()
        
        if ofertas_db.exists():
            # Procesar ofertas reales
            ofertas_list = []
            for oferta in ofertas_db:
                # Obtener productos relacionados
                productos = oferta.productos.all()
                
                # Variables para cálculos generales
                precio_total_original = Decimal('0')
                precio_total_con_descuento = Decimal('0')
                ahorro_total = Decimal('0')
                
                # Preparar datos de productos
                productos_data = []
                for producto in productos:
                    # Precio original del producto
                    precio_original = producto.precio
                    
                    # CALCULAR PRECIO CON DESCUENTO AUTOMÁTICAMENTE
                    # Usar el descuento de la oferta (campo 'descuento' en tu modelo)
                    porcentaje_descuento = oferta.descuento * 100  # Convertir 0.20 a 20%
                    
                    # Calcular precio con descuento
                    if oferta.descuento > 0:
                        # Multiplicar por el descuento decimal (0.20 = 20%)
                        descuento_decimal = oferta.descuento
                        monto_descuento = precio_original * descuento_decimal
                        precio_con_descuento = precio_original - monto_descuento
                        ahorro = monto_descuento
                    else:
                        precio_con_descuento = precio_original
                        ahorro = Decimal('0')
                    
                    # Acumular totales
                    precio_total_original += precio_original
                    precio_total_con_descuento += precio_con_descuento
                    ahorro_total += ahorro
                    
                    # Obtener URL de la imagen
                    imagen_url = producto.imagen.url if producto.imagen else None
                    
                    productos_data.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'precio': precio_original,
                        'precio_con_descuento': precio_con_descuento,
                        'descuento_porcentaje': porcentaje_descuento,  # 20% en lugar de 0.20
                        'ahorro': ahorro,
                        'imagen_url': imagen_url,
                        'tiene_imagen': bool(producto.imagen),
                    })
                
                # Determinar si está activa usando el método del modelo
                activo = oferta.activo()
                dias_restantes = oferta.dias_restantes()
                
                # Obtener imagen de la oferta (primera imagen de producto o default)
                imagen_oferta_url = None
                if productos_data and productos_data[0]['imagen_url']:
                    imagen_oferta_url = productos_data[0]['imagen_url']
                
                # Calcular porcentaje para mostrar (0.20 → 20%)
                porcentaje_mostrar = oferta.descuento * 100
                
                ofertas_list.append({
                    'id': oferta.id,
                    'nombre': oferta.nombre,
                    'descripcion': oferta.descripcion,
                    'descuento': oferta.descuento,  # 0.20
                    'descuento_porcentaje': porcentaje_mostrar,  # 20%
                    'fecha_inicio': oferta.fecha_inicio,
                    'fecha_fin': oferta.fecha_fin,
                    'activo': activo,
                    'dias_restantes': dias_restantes,
                    'productos': productos_data,
                    'imagen_url': imagen_oferta_url,
                    'tiene_imagen': bool(imagen_oferta_url),
                    'total_productos': len(productos_data),
                    
                    # Totales calculados
                    'precio_total_original': precio_total_original,
                    'precio_total_con_descuento': precio_total_con_descuento,
                    'ahorro_total': ahorro_total,
                    'precio_promedio_con_descuento': precio_total_con_descuento / len(productos_data) if productos_data else Decimal('0'),
                })
            
            ofertas = ofertas_list
            ofertas_activas = [o for o in ofertas_list if o['activo']]
            
        else:
            # Si no hay ofertas en la base de datos
            ofertas = []
            ofertas_activas = []
            
    except Exception as e:
        # En caso de error
        print(f"Error en vista ofertas: {str(e)}")
        ofertas = []
        ofertas_activas = []
    
    context = {
        'ofertas': ofertas,
        'hoy': hoy,
        'ofertas_activas': ofertas_activas,
    }
    
    return render(request, 'core/ofertas.html', context)
def producto_detail(request, pk):
    """Muestra el detalle de un producto"""
    producto = get_object_or_404(Producto, id=pk)
    
    # Verificar si está en oferta activa
    hoy = timezone.now().date()
    ofertas_activas = Oferta.objects.filter(
        productos=producto,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    ).order_by('-descuento')  # Ordenar por mayor descuento primero
    
    # Calcular precio con descuento si está en oferta
    precio_con_descuento = None
    porcentaje_descuento = None
    ahorro = None
    
    if ofertas_activas.exists():
        oferta = ofertas_activas.first()
        porcentaje_descuento = oferta.descuento * 100  # Convertir 0.20 a 20%
        precio_con_descuento = producto.precio * (Decimal(1) - oferta.descuento)
        ahorro = producto.precio - precio_con_descuento
    
    context = {
        'producto': producto,
        'ofertas_activas': ofertas_activas,
        'precio_con_descuento': precio_con_descuento,
        'porcentaje_descuento': porcentaje_descuento,
        'ahorro': ahorro,
    }
    
    return render(request, 'core/producto_detail.html', context)

# -----------------------------
# LOGIN / LOGOUT / REGISTRO
# -----------------------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Asegurarse de que el usuario tenga perfil
                from .models import PerfilUsuario
                PerfilUsuario.objects.get_or_create(usuario=user)
                
                login(request, user)
                
                messages.success(
                    request, 
                    f'¡Bienvenido {username}! '
                    'Disfruta de nuestras fragancias exclusivas y nuestras ofertas especiales.'
                )
                
                next_url = request.GET.get('next', 'inicio')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/login.html', {'form': form})
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("inicio")

# En views.py, función registro:
def registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, 
                f"¡Bienvenido a nuestra perfumería {user.username}! "
                "Tu cuenta ha sido creada exitosamente. "
                "Ahora puedes disfrutar de todas nuestras fragancias exclusivas."
            )
            
            # Redirigir a la página de donde vino o a inicio
            next_url = request.GET.get('next', 'inicio')
            return redirect(next_url)
    else:
        form = RegistroForm()

    return render(request, "core/registro.html", {"form": form})

# -----------------------------
# CARRITO
# -----------------------------
# core/views.py - función carrito
@login_required
def carrito(request):
    # Obtener el carrito MÁS RECIENTE
    carrito = Carrito.objects.filter(usuario=request.user).order_by('-creado').first()
    
    # Si no existe, crear uno nuevo
    if not carrito:
        carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
        carrito = Carrito.objects.create(usuario=request.user)
        return redirect('carrito')  # Recargar para mostrar carrito vacío
    
    # Recalcular precios si hay productos
    for item in carrito.items.all():
        if item.producto.tiene_descuento:
            nuevo_precio = item.producto.precio_con_descuento
            if item.precio_unitario != nuevo_precio:
                item.precio_unitario = nuevo_precio
                item.save()
    
    # Calcular todo
    subtotal_original = Decimal('0.00')
    subtotal_con_descuento = Decimal('0.00')
    descuento_total = Decimal('0.00')
    cantidad_items = 0
    
    for item in carrito.items.all():
        precio_original = item.producto.precio
        precio_actual = item.precio_unitario
        
        subtotal_original += precio_original * item.cantidad
        subtotal_con_descuento += precio_actual * item.cantidad
        
        if precio_original != precio_actual:
            descuento_total += (precio_original - precio_actual) * item.cantidad
        
        cantidad_items += item.cantidad
    
    # Impuesto
    impuesto_porcentaje = Decimal('0.16')
    impuesto = subtotal_con_descuento * impuesto_porcentaje
    
    # Envío
    envio = Decimal('0.00')
    calcular_envio_gratis = subtotal_con_descuento >= Decimal('500.00')
    faltante_envio_gratis = Decimal('0.00')
    
    if not calcular_envio_gratis:
        envio = Decimal('50.00')
        faltante_envio_gratis = Decimal('500.00') - subtotal_con_descuento
    
    # Total
    total = subtotal_con_descuento + impuesto + envio
    
    # Calcular productos faltantes para oferta
    productos_faltantes = 3 - cantidad_items if cantidad_items < 3 else 0
    
    return render(request, "core/carrito.html", {
        "carrito": carrito,
        "subtotal_original": subtotal_original,
        "subtotal_con_descuento": subtotal_con_descuento,
        "descuento_total": descuento_total,
        "impuesto": impuesto,
        "impuesto_porcentaje": impuesto_porcentaje * 100,
        "envio": envio,
        "total": total,
        "cantidad_items": cantidad_items,
        "calcular_envio_gratis": calcular_envio_gratis,
        "faltante_envio_gratis": faltante_envio_gratis,
        "productos_faltantes": productos_faltantes
    })

@login_required
def agregar_carrito(request, producto_id):
    """Agrega un producto individual al carrito"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Verificar stock
    if producto.stock <= 0:
        messages.error(request, "Este producto está agotado.")
        return redirect('producto_detail', pk=producto_id)
    
    # Obtener cantidad del formulario (por defecto 1)
    cantidad = int(request.POST.get('cantidad', 1))
    
    if cantidad <= 0:
        cantidad = 1
    
    if cantidad > producto.stock:
        messages.error(request, f"No hay suficiente stock. Disponible: {producto.stock}")
        return redirect('producto_detail', pk=producto_id)
    
    # IMPORTANTE: Usar precio_con_descuento que considera ofertas
    precio_final = producto.precio_con_descuento
    
    # Verificar tipo de descuento para el mensaje
    mensaje_descuento = ""
    if producto.tiene_descuento:
        # Determinar si es descuento directo o oferta
        oferta = producto.oferta_activa
        if oferta:
            descuento_porcentaje = oferta.descuento * 100
            mensaje_descuento = f" con {descuento_porcentaje:.0f}% de descuento (Oferta)"
        elif producto.descuento_porcentaje:
            mensaje_descuento = f" con {producto.descuento_porcentaje}% de descuento"
    
    # Obtener o crear carrito
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    
    # Verificar si ya está en el carrito
    item_existente = CarritoItem.objects.filter(
        carrito=carrito, 
        producto=producto
    ).first()
    
    if item_existente:
        # Actualizar cantidad
        item_existente.cantidad += cantidad
        item_existente.precio_unitario = precio_final  # ¡ACTUALIZAR PRECIO!
        item_existente.save()
        mensaje = f"Actualizada cantidad de {producto.nombre}{mensaje_descuento}"
    else:
        # Crear nuevo item en el carrito
        CarritoItem.objects.create(
            carrito=carrito,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio_final  # ¡GUARDAR CON DESCUENTO!
        )
        mensaje = f"¡{cantidad} {producto.nombre} agregado(s) al carrito{mensaje_descuento}!"
    
    messages.success(request, mensaje)
    return redirect('carrito')
@login_required
def agregar_oferta_carrito(request, oferta_id):
    """Agrega todos los productos de una oferta al carrito"""
    oferta = get_object_or_404(Oferta, id=oferta_id)
    
    # Verificar que la oferta esté activa
    if not oferta.activo():
        messages.error(request, "Esta oferta no está disponible actualmente.")
        return redirect('ofertas')
    
    # Obtener o crear el carrito del usuario
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    
    # Agregar cada producto de la oferta al carrito
    productos_agregados = 0
    for producto in oferta.productos.all():
        # Verificar stock
        if producto.stock <= 0:
            continue
        
        # Calcular precio con descuento de la oferta
        precio_con_descuento = producto.precio * (Decimal('1') - oferta.descuento)
        
        # Verificar si el producto ya está en el carrito
        item_existente = CarritoItem.objects.filter(
            carrito=carrito, 
            producto=producto
        ).first()
        
        if item_existente:
            # Actualizar cantidad y precio (siempre con precio de oferta)
            item_existente.cantidad += 1
            item_existente.precio_unitario = precio_con_descuento  # Forzar precio de oferta
            item_existente.save()
        else:
            # Crear nuevo item en el carrito
            CarritoItem.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=1,
                precio_unitario=precio_con_descuento  # Precio de oferta
            )
        
        productos_agregados += 1
    
    # Mensaje de éxito
    if productos_agregados > 0:
        descuento_porcentaje = oferta.descuento * 100
        messages.success(
            request, 
            f"¡{productos_agregados} producto(s) de la oferta '{oferta.nombre}' agregados al carrito con {descuento_porcentaje:.0f}% de descuento!"
        )
    else:
        messages.warning(request, "La oferta no tiene productos disponibles.")
    
    return redirect('carrito')
@login_required
def reparar_precios_carrito(request):
    """Repara todos los precios del carrito - USO TEMPORAL"""
    carrito = Carrito.objects.get(usuario=request.user)
    
    items_reparados = 0
    for item in carrito.items.all():
        precio_correcto = item.producto.precio_con_descuento
        
        # DEBUG: Mostrar información
        print(f"Producto: {item.producto.nombre}")
        print(f"  Precio original: {item.producto.precio}")
        print(f"  Precio con descuento: {precio_correcto}")
        print(f"  Precio actual en carrito: {item.precio_unitario}")
        print(f"  Tiene descuento: {item.producto.tiene_descuento}")
        print(f"  Descuento %: {item.producto.descuento_porcentaje_final}")
        
        if item.precio_unitario != precio_correcto:
            print(f"  ¡REPARANDO! Cambiando de {item.precio_unitario} a {precio_correcto}")
            item.precio_unitario = precio_correcto
            item.save()
            items_reparados += 1
    
    if items_reparados > 0:
        messages.success(request, f"¡{items_reparados} precios reparados en tu carrito!")
    else:
        messages.info(request, "Todos los precios en tu carrito ya son correctos.")
    
    return redirect('carrito')

@login_required
def cambiar_cantidad(request, item_id):
    """Cambiar cantidad en carrito"""
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    
    if request.method == "POST":
        nueva_cantidad = int(request.POST.get("cantidad", 1))
        
        if nueva_cantidad <= 0:
            item.delete()
        else:
            item.cantidad = nueva_cantidad
            item.save()
    
    return redirect("carrito")

@login_required
def eliminar_carrito(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    producto_nombre = item.producto.nombre
    item.delete()
    messages.success(request, f"{producto_nombre} eliminado del carrito.")
    return redirect("carrito")

@login_required
def cambiar_cantidad(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)

    if request.method == "POST":
        nueva_cantidad = int(request.POST.get("cantidad", 1))
        
        if nueva_cantidad <= 0:
            item.delete()
            messages.info(request, "Producto eliminado del carrito.")
        else:
            if nueva_cantidad > item.producto.stock:
                messages.error(request, "No hay suficiente stock disponible.")
                return redirect("carrito")
            
            item.cantidad = nueva_cantidad
            item.save()
            messages.info(request, "Cantidad actualizada.")

    return redirect("carrito")

# core/views.py - función checkout
# core/views.py - FUNCIÓN CHECKOUT QUE SÍ VACÍA EL CARRITO
from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Carrito, CarritoItem, Pedido, PedidoItem, Direccion
# core/views.py
@login_required
def checkout(request):
    try:
        # 1. Obtener el carrito del usuario
        carrito = Carrito.objects.filter(usuario=request.user).first()
        if not carrito:
            return redirect('carrito')
        
        carrito_items = carrito.items.all()
        
        # 2. Si no hay items, redirigir
        if not carrito_items:
            messages.error(request, 'El carrito está vacío')
            return redirect('carrito')
        
        # 3. Calcular total simple
        total = Decimal('0.00')
        for item in carrito_items:
            total += item.precio_unitario * item.cantidad
        
        # 4. Si es POST (cuando el usuario envía el formulario)
        if request.method == 'POST':
            # 5. Crear el pedido
            pedido = Pedido.objects.create(
                usuario=request.user,
                total=total,
                metodo_pago='Tarjeta',
                estado='Pendiente'
            )
            
            # 6. Copiar items al pedido
            for item in carrito_items:
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario
                )
            
            # 7. ¡¡¡VACIAR EL CARRITO AQUÍ!!!
            carrito.items.all().delete()  # <- ESTA LÍNEA ES CLAVE
            
            # 8. Redirigir a confirmación
            messages.success(request, f'Pedido #{pedido.id} creado')
            return redirect('confirmacion_pedido', pedido_id=pedido.id)
        
        # 9. Mostrar formulario
        return render(request, 'core/checkout.html', {
            'total': total
        })
        
    except Exception as e:
        messages.error(request, 'Error en checkout')
        return redirect('carrito')

@login_required
def confirmacion_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    return render(request, "core/confirmacion_pedido.html", {
        "pedido": pedido
    })
def vaciar_carrito_usuario(usuario):
    """Vacía completamente el carrito de un usuario"""
    try:
        carrito = Carrito.objects.get(usuario=usuario)
        # Contar items antes de vaciar
        items_count = carrito.items.count()
        
        # Vaciar
        carrito.items.all().delete()
        
        # Verificar que se vació
        if carrito.items.count() == 0:
            print(f"✓ Carrito de {usuario.username} vaciado correctamente. Se eliminaron {items_count} items.")
            return True
        else:
            print(f"✗ Error: Carrito de {usuario.username} no se vació. Items restantes: {carrito.items.count()}")
            return False
            
    except Carrito.DoesNotExist:
        print(f"✗ Carrito de {usuario.username} no existe")
        return False
    except Exception as e:
        print(f"✗ Error al vaciar carrito: {e}")
        return False
    print(f"DEBUG: Usuario: {request.user.username}")
    print(f"DEBUG: Carrito ID: {carrito.id}")
    print(f"DEBUG: Items antes de vaciar: {carrito.items.count()}")
    carrito.items.all().delete()
    print(f"DEBUG: Items después de vaciar: {carrito.items.count()}")
    print(f"DEBUG: Verificando de nuevo: {Carrito.objects.get(id=carrito.id).items.count()}")
    


def contacto(request):
    """Vista simple de contacto"""
    return render(request, 'core/contacto.html')
# -----------------------------
# ADMIN CUSTOM
# -----------------------------
@login_required
@staff_member_required
def admin_dashboard(request):
    """Panel de control principal del admin"""
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    total_usuarios = Usuario.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='Pendiente').count()
    
    productos_bajo_stock = Producto.objects.filter(stock__lt=10)[:5]
    ultimos_pedidos = Pedido.objects.order_by('-fecha')[:5]
    
    return render(request, "admin/dashboard.html", {
        "total_productos": total_productos,
        "total_pedidos": total_pedidos,
        "total_usuarios": total_usuarios,
        "pedidos_pendientes": pedidos_pendientes,
        "productos_bajo_stock": productos_bajo_stock,
        "ultimos_pedidos": ultimos_pedidos,
    })

# PRODUCTOS
@login_required
@staff_member_required
def admin_productos(request):
    productos = Producto.objects.all().select_related('marca', 'categoria')
    
    # Datos para estadísticas
    productos_con_stock = productos.filter(stock__gt=0).count()
    marcas_count = Marca.objects.count()
    categorias_count = Categoria.objects.count()
    productos_agotados = productos.filter(stock=0).count()
    
    return render(request, "admin/productos.html", {
        "productos": productos,
        "productos_con_stock": productos_con_stock,
        "marcas_count": marcas_count,
        "categorias_count": categorias_count,
        "productos_agotados": productos_agotados
    })

@login_required
@staff_member_required
def admin_producto_agregar(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" agregado exitosamente.')
            return redirect("admin_productos")
    else:
        form = ProductoForm()
    
    return render(request, "admin/agregar_producto.html", {
        "form": form,
        "titulo": "Nuevo Producto"
    })

@login_required
@staff_member_required
def admin_producto_editar(request, id):
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect("admin_productos")
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, "admin/editar_producto.html", {
        "form": form,
        "producto": producto,
        "titulo": f"Editar: {producto.nombre}"
    })

@login_required
@staff_member_required
def admin_producto_eliminar(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto_nombre = producto.nombre
    
    if request.method == "POST":
        producto.delete()
        messages.success(request, f'Producto "{producto_nombre}" eliminado exitosamente.')
        return redirect("admin_productos")
    
    return render(request, "admin/eliminar_producto.html", {
        "producto": producto
    })

# CATEGORÍAS
@login_required
@staff_member_required
def admin_categorias(request):
    categorias = Categoria.objects.all()
    productos_por_categoria = Producto.objects.filter(categoria__in=categorias).count()
    
    return render(request, "admin/categorias.html", {
        "categorias": categorias,
        "productos_por_categoria": productos_por_categoria,
        "categorias_sin_productos": categorias.filter(productos__isnull=True).count(),
    })

@login_required
@staff_member_required
def admin_categoria_agregar(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" agregada exitosamente.')
            return redirect("admin_categorias")
    else:
        form = CategoriaForm()
    
    return render(request, "admin/agregar_categoria.html", {
        "form": form,
        "titulo": "Nueva Categoría"
    })

@login_required
@staff_member_required
def admin_categoria_editar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            return redirect("admin_categorias")
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, "admin/editar_categoria.html", {
        "form": form,
        "categoria": categoria,
        "titulo": f"Editar: {categoria.nombre}"
    })

@login_required
@staff_member_required
def admin_categoria_eliminar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    categoria_nombre = categoria.nombre
    
    if request.method == "POST":
        categoria.delete()
        messages.success(request, f'Categoría "{categoria_nombre}" eliminada exitosamente.')
        return redirect("admin_categorias")
    
    return render(request, "admin/eliminar_categoria.html", {
        "categoria": categoria
    })

# MARCAS
@login_required
@login_required
@staff_member_required
def admin_marcas(request):
    marcas = Marca.objects.all()
    productos_por_marca = Producto.objects.filter(marca__in=marcas).count()
    paises = set(marca.pais_origen for marca in marcas if marca.pais_origen)
    
    return render(request, "admin/marcas.html", {
        "marcas": marcas,
        "productos_por_marca": productos_por_marca,
        "paises_count": len(paises),
        "marcas_con_imagen": marcas.filter(imagen__isnull=False).count(),
        "total_productos": productos_por_marca,
    })

@login_required
@staff_member_required
def admin_marca_agregar(request):
    if request.method == "POST":
        form = MarcaForm(request.POST, request.FILES)
        if form.is_valid():
            marca = form.save()
            messages.success(request, f'Marca "{marca.nombre}" agregada exitosamente.')
            return redirect("admin_marcas")
    else:
        form = MarcaForm()
    
    return render(request, "admin/agregar_marca.html", {
        "form": form,
        "titulo": "Nueva Marca"
    })

@login_required
@staff_member_required
def admin_marca_editar(request, id):
    marca = get_object_or_404(Marca, id=id)
    
    if request.method == "POST":
        form = MarcaForm(request.POST, request.FILES, instance=marca)
        if form.is_valid():
            marca = form.save()
            messages.success(request, f'Marca "{marca.nombre}" actualizada exitosamente.')
            return redirect("admin_marcas")
    else:
        form = MarcaForm(instance=marca)
    
    return render(request, "admin/editar_marca.html", {
        "form": form,
        "marca": marca,
        "titulo": f"Editar: {marca.nombre}"
    })

@login_required
@staff_member_required
def admin_marca_eliminar(request, id):
    marca = get_object_or_404(Marca, id=id)
    marca_nombre = marca.nombre
    
    if request.method == "POST":
        marca.delete()
        messages.success(request, f'Marca "{marca_nombre}" eliminada exitosamente.')
        return redirect("admin_marcas")
    
    return render(request, "admin/eliminar_marca.html", {
        "marca": marca
    })

# OFERTAS
@login_required
@staff_member_required
def admin_ofertas(request):
    ofertas = Oferta.objects.all()
    hoy = timezone.now().date()
    
    ofertas_activas = []
    ofertas_pendientes = 0
    ofertas_expiradas = 0
    
    for oferta in ofertas:
        if oferta.fecha_inicio <= hoy <= oferta.fecha_fin:
            ofertas_activas.append(oferta)
            oferta.dias_restantes = (oferta.fecha_fin - hoy).days
        elif oferta.fecha_inicio > hoy:
            ofertas_pendientes += 1
        else:
            ofertas_expiradas += 1
    
    return render(request, "admin/ofertas.html", {
        "ofertas": ofertas,
        "ofertas_activas": ofertas_activas,
        "ofertas_pendientes": ofertas_pendientes,
        "ofertas_expiradas": ofertas_expiradas,
        "hoy": hoy,
    })

@login_required
@staff_member_required
def admin_oferta_agregar(request):
    if request.method == "POST":
        form = OfertaForm(request.POST)
        if form.is_valid():
            oferta = form.save()
            messages.success(request, f'Oferta "{oferta.nombre}" agregada exitosamente.')
            return redirect("admin_ofertas")
    else:
        form = OfertaForm()
    
    return render(request, "admin/agregar_oferta.html", {
        "form": form,
        "titulo": "Nueva Oferta"
    })

@login_required
@staff_member_required
def admin_oferta_editar(request, id):
    oferta = get_object_or_404(Oferta, id=id)
    
    if request.method == "POST":
        form = OfertaForm(request.POST, instance=oferta)
        if form.is_valid():
            oferta = form.save()
            messages.success(request, f'Oferta "{oferta.nombre}" actualizada exitosamente.')
            return redirect("admin_ofertas")
    else:
        form = OfertaForm(instance=oferta)
    
    return render(request, "admin/editar_oferta.html", {
        "form": form,
        "oferta": oferta,
        "titulo": f"Editar: {oferta.nombre}"
    })

@login_required
@staff_member_required
def admin_oferta_eliminar(request, id):
    oferta = get_object_or_404(Oferta, id=id)
    oferta_nombre = oferta.nombre
    
    if request.method == "POST":
        oferta.delete()
        messages.success(request, f'Oferta "{oferta_nombre}" eliminada exitosamente.')
        return redirect("admin_ofertas")
    
    return render(request, "admin/eliminar_oferta.html", {
        "oferta": oferta
    })

# USUARIOS ADMIN
@login_required
@staff_member_required
def admin_usuarios(request):
    usuarios = Usuario.objects.all()
    usuarios_con_pedidos = usuarios.filter(pedidos__isnull=False).distinct().count()
    
    return render(request, "admin/usuarios.html", {
        "usuarios": usuarios,
        "usuarios_count": usuarios.count(),
        "staff_count": usuarios.filter(is_staff=True).count(),
        "usuarios_con_pedidos": usuarios_con_pedidos,
    })

@login_required
@staff_member_required
def admin_usuario_editar(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    
    if request.method == "POST":
        # Aquí puedes crear un formulario para editar usuarios
        is_staff = request.POST.get('is_staff') == 'on'
        usuario.is_staff = is_staff
        usuario.save()
        
        messages.success(request, f'Usuario "{usuario.username}" actualizado exitosamente.')
        return redirect("admin_usuarios")
    
    return render(request, "admin/editar_usuario.html", {
        "usuario": usuario
    })

@login_required
@staff_member_required
def admin_usuario_eliminar(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario_nombre = usuario.username
    
    if request.method == "POST":
        usuario.delete()
        messages.success(request, f'Usuario "{usuario_nombre}" eliminado exitosamente.')
        return redirect("admin_usuarios")
    
    return render(request, "admin/eliminar_usuario.html", {
        "usuario": usuario
    })

# PEDIDOS
@login_required
@staff_member_required
def admin_pedidos(request):
    pedidos = Pedido.objects.all().order_by('-fecha')
    
    estados = Pedido.ESTADO
    filtro_estado = request.GET.get('estado')
    
    if filtro_estado:
        pedidos = pedidos.filter(estado=filtro_estado)
    
    # Estadísticas
    pedidos_pendientes = Pedido.objects.filter(estado='Pendiente').count()
    pedidos_entregados = Pedido.objects.filter(estado='Entregado').count()
    total_ventas = sum(pedido.total for pedido in pedidos)
    
    return render(request, "admin/pedidos.html", {
        "pedidos": pedidos,
        "estados": estados,
        "estado_actual": filtro_estado,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_entregados": pedidos_entregados,
        "total_ventas": total_ventas,
    })

@login_required
@staff_member_required
def admin_pedido_detalle(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    
    if request.method == "POST":
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Pedido.ESTADO):
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Estado del pedido #{pedido.id} actualizado a {nuevo_estado}.')
    
    return render(request, "admin/pedido_detail.html", {
        "pedido": pedido
    })

@login_required
@staff_member_required
def admin_pedido_eliminar(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    pedido_id = pedido.id
    
    if request.method == "POST":
        pedido.delete()
        messages.success(request, f'Pedido #{pedido_id} eliminado exitosamente.')
        return redirect("admin_pedidos")
    
    return render(request, "admin/eliminar_pedido.html", {
        "pedido": pedido
    })