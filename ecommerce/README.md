# E-commerce Backend API

A complete e-commerce backend built with Django REST Framework, featuring JWT authentication, an AI-powered chatbot using Claude API, and async task processing with Celery.

## Features

- **User Authentication**: JWT-based authentication with registration, login, logout, and profile management
- **Product Management**: Full CRUD operations with search, filtering, and pagination
- **Order Management**: Create orders, track status, manage order items
- **Payment Processing**: Multiple payment methods, apply payments to orders
- **Shipment Tracking**: Track shipments, generate tracking numbers, status updates
- **AI Chatbot**: Claude-powered assistant for order inquiries
- **Async Tasks**: Celery-based notifications for shipment updates
- **API Documentation**: Swagger/OpenAPI documentation

## Tech Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Database**: SQLite (development)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Async Tasks**: Celery + Redis
- **AI**: Anthropic Claude API
- **Testing**: pytest + pytest-django
- **Documentation**: drf-spectacular (Swagger/OpenAPI)

## Project Structure

```
ecommerce/
├── config/                 # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── celery.py          # Celery configuration
├── apps/
│   ├── users/             # User authentication
│   ├── products/          # Product management
│   ├── orders/            # Order management
│   ├── payments/          # Payment processing
│   ├── shipments/         # Shipment tracking
│   └── chatbot/           # AI chatbot
├── core/                   # Shared utilities
│   ├── pagination.py      # Custom pagination
│   ├── permissions.py     # Custom permissions
│   └── repositories.py    # Base repository pattern
├── reports/
│   └── orders_report.sql  # SQL reports
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Installation

### Local Development

1. **Clone the repository**:
   ```bash
   cd ecommerce
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

8. **Access the API**:
   - API: http://localhost:8000/api/
   - Swagger docs: http://localhost:8000/api/docs/
   - Admin: http://localhost:8000/admin/

### Running with Docker

1. **Build and start containers**:
   ```bash
   docker-compose up --build
   ```

2. **Run migrations** (if needed):
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Running Celery (Local)

```bash
# Start Redis (if not using Docker)
redis-server

# Start Celery worker
celery -A config worker -l INFO

# Start Celery beat (for scheduled tasks)
celery -A config beat -l INFO
```

## API Endpoints

### Authentication
- `POST /api/users/register/` - Register new user
- `POST /api/users/login/` - Login (get JWT tokens)
- `POST /api/users/logout/` - Logout (blacklist token)
- `POST /api/users/token/refresh/` - Refresh access token
- `GET/PATCH /api/users/profile/` - User profile

### Products
- `GET /api/products/` - List products
- `POST /api/products/` - Create product (admin)
- `GET /api/products/{id}/` - Get product details
- `PUT/PATCH /api/products/{id}/` - Update product (admin)
- `DELETE /api/products/{id}/` - Delete product (admin)

### Orders
- `GET /api/orders/` - List orders
- `POST /api/orders/` - Create order
- `GET /api/orders/{id}/` - Get order details
- `PATCH /api/orders/{id}/status/` - Update order status
- `GET /api/orders/my-orders/` - Get current user's orders

### Payments
- `GET /api/payments/` - List payments
- `POST /api/payments/` - Create payment
- `GET /api/payments/{id}/` - Get payment details
- `POST /api/payments/{id}/apply/` - Apply payment to orders
- `POST /api/payments/{id}/complete/` - Mark payment as completed
- `POST /api/payments/{id}/fail/` - Mark payment as failed

### Shipments
- `GET /api/shipments/` - List shipments
- `POST /api/shipments/` - Create shipment (admin)
- `GET /api/shipments/{id}/` - Get shipment details
- `POST /api/shipments/{id}/ship/` - Mark as shipped
- `POST /api/shipments/{id}/deliver/` - Mark as delivered
- `GET /api/shipments/by-order/{order_id}/` - Get shipments by order
- `GET /api/shipments/track/{tracking_number}/` - Track by tracking number

### Chatbot
- `POST /api/chat/` - Send message to AI assistant

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps

# Run specific app tests
pytest apps/users/tests.py -v
```

## Example Usage

### Register a User
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Create an Order
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ]
  }'
```

### Chat with AI Assistant
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of my order #1?"}'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | - |
| `DEBUG` | Debug mode | True |
| `ALLOWED_HOSTS` | Allowed hosts | localhost,127.0.0.1 |
| `CELERY_BROKER_URL` | Redis URL for Celery | redis://localhost:6379/0 |
| `ANTHROPIC_API_KEY` | Claude API key | - |

## License

MIT License
