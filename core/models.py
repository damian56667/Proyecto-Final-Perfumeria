from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# Si quieres usuario personalizado con campos extra:
class Usuario(AbstractUser):
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.username

User = settings.AUTH_USER_MODEL  # string cuando se usa AUTH_USER_MODEL
# NOTA: settings.AUTH_USER_MODEL = 'core.Usuario' en settings.py .env

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def crear_perfil_usuario(sender, instance, created, **kwargs):
        if created:
            PerfilUsuario.objects.create(usuario=instance)

    @receiver(post_save, sender=User)
    def guardar_perfil_usuario(sender, instance, **kwargs):
            instance.perfil.save()
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    def __str__(self):
        return self.nombre

class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    pais_origen = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='marcas/', blank=True, null=True)

    def __str__(self):
        return self.nombre


    def __str__(self):
        return self.nombre
    
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea un perfil automáticamente cuando se crea un nuevo usuario
    """
    if created:
        PerfilUsuario.objects.create(usuario=instance)

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        blank=True,
        null=True,
        verbose_name="Descuento (%)"
    )
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, blank=True, null=True)
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name='productos')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    

    @property
    def tiene_descuento(self):
        """Verifica si el producto tiene descuento (de cualquier tipo)"""
        # 1. Descuento directo
        if self.descuento_porcentaje and float(self.descuento_porcentaje) > 0:
            return True
        
        # 2. Oferta activa
        hoy = timezone.now().date()
        if self.ofertas.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy).exists():
            return True
        
        return False
    
    @property
    def oferta_activa(self):
        """Obtiene la oferta activa si existe"""
        hoy = timezone.now().date()
        ofertas = self.ofertas.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy)
        return ofertas.first() if ofertas.exists() else None
    
    @property
    def precio_con_descuento(self):
        """Calcula el precio con el mejor descuento disponible"""
        precio_final = self.precio
        descuento_aplicado = 0
        
        # 1. Verificar si tiene descuento directo
        if self.descuento_porcentaje and float(self.descuento_porcentaje) > 0:
            descuento = self.precio * (self.descuento_porcentaje / Decimal('100'))
            precio_final = self.precio - descuento
            descuento_aplicado = self.descuento_porcentaje
        
        # 2. Verificar si tiene oferta activa (tiene prioridad si es mayor)
        oferta = self.oferta_activa
        if oferta:
            precio_oferta = self.precio * (Decimal('1') - oferta.descuento)
            # Usar la oferta si es mejor (precio más bajo)
            if precio_oferta < precio_final:
                precio_final = precio_oferta
                descuento_aplicado = oferta.descuento * 100  # Convertir a porcentaje
        
        return precio_final
    
    @property
    def descuento_porcentaje_final(self):
        """Obtiene el porcentaje de descuento que se está aplicando"""
        if not self.tiene_descuento:
            return 0
        
        # Calcular qué porcentaje representa el descuento
        if self.precio > 0:
            descuento_absoluto = self.precio - self.precio_con_descuento
            porcentaje = (descuento_absoluto / self.precio) * 100
            return round(porcentaje, 2)
        return 0
    
    @property
    def ahorro(self):
        """Calcula cuánto se ahorra con el descuento"""
        if self.tiene_descuento:
            return self.precio - self.precio_con_descuento
        return Decimal('0')
    
class Oferta(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    descuento = models.DecimalField(max_digits=4, decimal_places=2, help_text="usar 0.20 para 20%")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    productos = models.ManyToManyField(Producto, blank=True, related_name='ofertas')

    def activo(self):
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin
    
    def dias_restantes(self):
        """Calcula los días restantes de la oferta"""
        hoy = timezone.now().date()
        if self.fecha_fin >= hoy:
            return (self.fecha_fin - hoy).days
        return 0
    def estado(self):
        """Retorna el estado de la oferta"""
        hoy = timezone.now().date()
        if self.fecha_inicio > hoy:
            return 'próxima'
        elif self.fecha_fin < hoy:
            return 'expirada'
        else:
            return 'activa'


    def __str__(self):
        return self.nombre

class Direccion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direcciones')
    calle = models.CharField(max_length=250)
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20)
    pais = models.CharField(max_length=80, default='México')
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.calle}, {self.ciudad}"

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')  # Cambiado a OneToOneField
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"
    
    def total_sin_impuestos(self):
        total = sum(item.subtotal() for item in self.items.all())
        return round(total, 2)
    
    def impuestos(self, tasa=0.16):
        return round(self.total_sin_impuestos() * tasa, 2)
    
    def total_con_impuestos(self, tasa=0.16):
        return round(self.total_sin_impuestos() + self.impuestos(tasa), 2)
    
    def vaciar(self):
        """Vacía todos los items del carrito"""
        self.items.all().delete()
        return True

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return round(self.cantidad * float(self.precio_unitario), 2)

class Pedido(models.Model):
    ESTADO = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos')
    direccion_envio = models.ForeignKey(Direccion, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO, default='Pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    metodo_pago = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario}"

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return round(self.cantidad * float(self.precio_unitario), 2)
    

class Pago(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pago')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)
    detalles = models.TextField(blank=True)

    def __str__(self):
        return f"Pago pedido {self.pedido.id} - {self.monto}"
