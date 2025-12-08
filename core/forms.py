import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Marca, Categoria, Producto, Oferta, Pedido
from .models import PerfilUsuario


User = get_user_model()

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'tu@correo.com'
    }))
    telefono = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ej: 555-1234567'
    }))
    direccion = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Ingresa tu dirección completa',
        'rows': 3
    }), required=False)
    ciudad = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ej: Ciudad de México'
    }))
    terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'Debes aceptar los términos y condiciones'}
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'telefono', 'direccion', 'ciudad', 'password1', 'password2']
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Elige un nombre de usuario'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases a los campos de contraseña
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Crea una contraseña segura'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Repite tu contraseña'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Guardar datos adicionales en el perfil
            from .models import PerfilUsuario

            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil = user.perfil
            perfil.telefono = self.cleaned_data.get('telefono', '')
            perfil.direccion = self.cleaned_data.get('direccion', '')
            perfil.ciudad = self.cleaned_data.get('ciudad', '')
            perfil.save()
        
        return user
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email

# En forms.py, añade o actualiza la clase CheckoutForm:
class CheckoutForm(forms.Form):
    # Métodos de pago simulados
    METODO_PAGO_CHOICES = [
        ('simulado', '💳 Pago Simulado (Demo)'),
        ('tarjeta_simulada', '💳 Tarjeta de Crédito/Débito (Simulado)'),
        ('paypal_simulado', '💰 PayPal (Simulado)'),
        ('transferencia_simulada', '🏦 Transferencia Bancaria (Simulada)'),
    ]
    
    # Información personal
    nombre_completo = forms.CharField(
        max_length=200,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Pérez'
        })
    )
    
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com'
        })
    )
    
    telefono = forms.CharField(
        max_length=20,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 555-123-4567'
        })
    )
    
    # Dirección
    calle = forms.CharField(
        max_length=250,
        label='Calle y número',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Av. Principal #123'
        })
    )
    
    colonia = forms.CharField(
        max_length=150,
        label='Colonia',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Centro'
        })
    )
    
    ciudad = forms.CharField(
        max_length=100,
        label='Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Ciudad de México'
        })
    )
    
    estado = forms.CharField(
        max_length=100,
        label='Estado',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: CDMX'
        })
    )
    
    codigo_postal = forms.CharField(
        max_length=20,
        label='Código Postal',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 01000'
        })
    )
    
    # Método de pago
    metodo_pago = forms.ChoiceField(
        choices=METODO_PAGO_CHOICES,
        label='Método de pago',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='simulado'
    )
    
    # Campos para tarjeta (condicionales)
    nombre_tarjeta = forms.CharField(
        max_length=100,
        label='Nombre en la tarjeta',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Como aparece en la tarjeta'
        })
    )
    
    numero_tarjeta = forms.CharField(
        max_length=19,
        label='Número de tarjeta',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'data-mask': '0000 0000 0000 0000'
        })
    )
    
    fecha_expiracion = forms.CharField(
        max_length=5,
        label='Fecha expiración (MM/AA)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/AA',
            'style': 'width: 120px;'
        })
    )
    
    cvv = forms.CharField(
        max_length=4,
        label='CVV',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'style': 'width: 100px;'
        })
    )
    
    # Notas adicionales
    notas = forms.CharField(
        label='Notas adicionales (opcional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Instrucciones especiales para la entrega...'
        })
    )
    
    terminos = forms.BooleanField(
        label='Acepto los términos y condiciones',
        error_messages={'required': 'Debes aceptar los términos y condiciones'}
    )
    
    def clean(self):
        cleaned_data = super().clean()
        metodo_pago = cleaned_data.get('metodo_pago')
        
        # Validaciones para pago con tarjeta simulada
        if metodo_pago == 'tarjeta_simulada':
            # Validar que los campos de tarjeta estén completos
            required_fields = ['nombre_tarjeta', 'numero_tarjeta', 'fecha_expiracion', 'cvv']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'Este campo es requerido para pago con tarjeta')
            
            # Validar formato de fecha
            fecha = cleaned_data.get('fecha_expiracion', '')
            if fecha:
                if not re.match(r'^\d{2}/\d{2}$', fecha):
                    self.add_error('fecha_expiracion', 'Formato inválido. Use MM/AA')
        
        return cleaned_data
    
    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta', '').replace(' ', '')
        if numero:
            # Validación básica para demostración
            if len(numero) < 16:
                raise forms.ValidationError('El número de tarjeta debe tener al menos 16 dígitos')
            if not numero.isdigit():
                raise forms.ValidationError('Solo se permiten números')
        return numero
    
    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv', '')
        if cvv:
            if not cvv.isdigit():
                raise forms.ValidationError('El CVV debe contener solo números')
            if len(cvv) not in [3, 4]:
                raise forms.ValidationError('CVV debe tener 3 o 4 dígitos')
        return cvv
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        # Validación simple de teléfono
        if telefono and not re.match(r'^[\d\s\-\+\(\)]{7,20}$', telefono):
            raise forms.ValidationError('Formato de teléfono inválido')
        return telefono

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['nombre','pais_origen','descripcion','imagen']

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre','slug']

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre','slug','descripcion','precio','stock','sku','marca','categoria','imagen']

class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ['nombre','descripcion','descuento','fecha_inicio','fecha_fin','productos']

class PedidoAdminForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['usuario','direccion_envio','estado','metodo_pago','total']
