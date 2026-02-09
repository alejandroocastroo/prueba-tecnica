"""
Script para poblar la base de datos con datos de prueba.
Ejecutar: python seed_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, OrderPayment
from apps.shipments.models import Shipment

User = get_user_model()

def create_users():
    """Crear usuarios de prueba."""
    print("Creando usuarios...")

    # Admin
    admin, created = User.objects.get_or_create(
        email='admin@tienda.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Sistema',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"  [OK] Admin creado: admin@tienda.com / admin123")
    else:
        print(f"  [-] Admin ya existe: admin@tienda.com")

    # Usuario normal
    user, created = User.objects.get_or_create(
        email='cliente@test.com',
        defaults={
            'first_name': 'Juan',
            'last_name': 'Perez'
        }
    )
    if created:
        user.set_password('cliente123')
        user.save()
        print(f"  [OK] Cliente creado: cliente@test.com / cliente123")
    else:
        print(f"  [-] Cliente ya existe: cliente@test.com")

    return admin, user


def create_products():
    """Crear productos de prueba."""
    print("\nCreando productos...")

    products_data = [
        {
            'name': 'Laptop HP Pavilion',
            'description': 'Laptop HP Pavilion 15.6" Intel Core i5, 8GB RAM, 256GB SSD',
            'price': Decimal('899.99'),
            'stock': 15,
            'is_active': True
        },
        {
            'name': 'Mouse Logitech MX Master',
            'description': 'Mouse inalámbrico ergonómico con sensor de alta precisión',
            'price': Decimal('99.99'),
            'stock': 50,
            'is_active': True
        },
        {
            'name': 'Teclado Mecánico RGB',
            'description': 'Teclado mecánico con switches Cherry MX Blue e iluminación RGB',
            'price': Decimal('149.99'),
            'stock': 30,
            'is_active': True
        },
        {
            'name': 'Monitor Samsung 27"',
            'description': 'Monitor LED 27 pulgadas Full HD 75Hz',
            'price': Decimal('299.99'),
            'stock': 20,
            'is_active': True
        },
        {
            'name': 'Audífonos Sony WH-1000XM4',
            'description': 'Audífonos inalámbricos con cancelación de ruido',
            'price': Decimal('349.99'),
            'stock': 25,
            'is_active': True
        },
        {
            'name': 'Webcam Logitech C920',
            'description': 'Webcam Full HD 1080p con micrófono integrado',
            'price': Decimal('79.99'),
            'stock': 40,
            'is_active': True
        },
        {
            'name': 'SSD Samsung 1TB',
            'description': 'Disco de estado sólido NVMe M.2 1TB',
            'price': Decimal('129.99'),
            'stock': 35,
            'is_active': True
        },
        {
            'name': 'Cable HDMI 2.1',
            'description': 'Cable HDMI 2.1 4K 120Hz 2 metros',
            'price': Decimal('19.99'),
            'stock': 100,
            'is_active': True
        },
        {
            'name': 'Hub USB-C',
            'description': 'Hub USB-C 7 en 1 con HDMI, USB 3.0 y lector SD',
            'price': Decimal('49.99'),
            'stock': 45,
            'is_active': True
        },
        {
            'name': 'Smartphone Samsung Galaxy (AGOTADO)',
            'description': 'Samsung Galaxy S23 Ultra 256GB',
            'price': Decimal('1199.99'),
            'stock': 0,  # Sin stock
            'is_active': True
        },
    ]

    products = []
    for data in products_data:
        product, created = Product.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        products.append(product)
        if created:
            print(f"  [OK] {product.name} - ${product.price}")
        else:
            print(f"  [-] {product.name} ya existe")

    return products


def create_sample_order(user, products):
    """Crear un pedido de ejemplo."""
    print("\nCreando pedido de ejemplo...")

    # Verificar si ya existe un pedido para este usuario
    existing_order = Order.objects.filter(user=user).first()
    if existing_order:
        print(f"  - Ya existe pedido #{existing_order.id} para {user.email}")
        return existing_order

    # Crear pedido
    order = Order.objects.create(user=user)

    # Agregar items (laptop + mouse + teclado)
    items = [
        (products[0], 1),  # Laptop x1
        (products[1], 2),  # Mouse x2
        (products[2], 1),  # Teclado x1
    ]

    for product, qty in items:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            unit_price=product.price
        )
        # Reducir stock
        product.stock -= qty
        product.save()

    order.calculate_total()
    print(f"  [OK] Pedido #{order.id} creado - Total: ${order.total}")
    print(f"    Items: {', '.join([f'{i[1]}x {i[0].name}' for i in items])}")

    return order


def create_sample_payment(order):
    """Crear un pago de ejemplo."""
    print("\nCreando pago de ejemplo...")

    # Verificar si ya existe un pago para este pedido
    existing = OrderPayment.objects.filter(order=order).first()
    if existing:
        print(f"  - Ya existe pago para el pedido #{order.id}")
        return existing.payment

    # Crear pago
    payment = Payment.objects.create(
        amount=order.total,
        method=Payment.Method.CARD,
        status=Payment.Status.COMPLETED
    )

    # Aplicar a la orden
    OrderPayment.objects.create(
        order=order,
        payment=payment,
        amount_applied=order.total
    )

    # Actualizar estado del pedido
    order.status = Order.Status.PAID
    order.save()

    print(f"  [OK] Pago #{payment.id} creado - ${payment.amount} (tarjeta)")
    print(f"    Pedido #{order.id} ahora está PAGADO")

    return payment


def create_sample_shipment(order):
    """Crear un envío de ejemplo."""
    print("\nCreando envío de ejemplo...")

    # Verificar si ya existe envío
    existing = Shipment.objects.filter(order=order).first()
    if existing:
        print(f"  - Ya existe envío para el pedido #{order.id}")
        return existing

    # Crear envío
    shipment = Shipment.objects.create(order=order)
    shipment.mark_as_shipped()

    print(f"  [OK] Envío #{shipment.id} creado")
    print(f"    Tracking: {shipment.tracking_number}")
    print(f"    Pedido #{order.id} ahora está ENVIADO")

    return shipment


def main():
    print("=" * 50)
    print("POBLANDO BASE DE DATOS CON DATOS DE PRUEBA")
    print("=" * 50)

    admin, user = create_users()
    products = create_products()

    # Crear un pedido completo para el usuario de prueba
    order = create_sample_order(user, products)
    payment = create_sample_payment(order)
    shipment = create_sample_shipment(order)

    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"""
USUARIOS CREADOS:
  - Admin: admin@tienda.com / admin123
  - Cliente: cliente@test.com / cliente123

PRODUCTOS: {Product.objects.count()} productos

PEDIDO DE EJEMPLO:
  - Pedido #{order.id} - {user.email}
  - Estado: {order.status}
  - Total: ${order.total}
  - Tracking: {shipment.tracking_number}

PARA PROBAR:
  1. Ir a http://127.0.0.1:8000/api/docs/
  2. Login con cliente@test.com / cliente123
  3. Usar el access token para autorizar
  4. Probar los endpoints
""")


if __name__ == '__main__':
    main()
