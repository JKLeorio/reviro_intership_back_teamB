import os
import stripe
from dotenv import load_dotenv
import asyncio
import httpx
from datetime import datetime


load_dotenv()
# Настройка Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
print(os.getenv("STRIPE_SECRET_KEY"))  # Должно вывести ключ

async def test_stripe_connection():
    """Тест подключения к Stripe"""
    try:
        # Проверяем подключение через создание тестового продукта
        product = stripe.Product.create(
            name="Test Product",
            description="Test product for connection check"
        )

        price = stripe.Price.create(
            product=product.id,
            unit_amount=1000,  # $10.00
            currency='usd'
        )

        print("✅ Stripe connection successful!")
        print(f"Test Product ID: {product.id}")
        print(f"Test Price ID: {price.id}")

        # Удаляем тестовый продукт
        stripe.Product.modify(product.id, active=False)
        print("✅ Test product cleaned up")

        return True

    except Exception as e:
        print(f"❌ Stripe connection failed: {e}")
        return False


async def test_checkout_session():
    """Тест создания checkout session"""
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Test Course',
                    },
                    'unit_amount': 2000,  # $20.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            customer_email='test@example.com',
        )

        print("✅ Checkout session created successfully!")
        print(f"Session ID: {checkout_session.id}")
        print(f"Checkout URL: {checkout_session.url}")

        return checkout_session

    except Exception as e:
        print(f"❌ Checkout session creation failed: {e}")
        return None


async def test_api_endpoint():
    """Тест API эндпоинта (требует запущенного сервера)"""
    try:
        # Предполагаем что сервер запущен на localhost:8000
        async with httpx.AsyncClient() as client:
            # Тестовые данные - замените на реальные UUID и токен
            test_data = {
                "subscription_id": "123e4567-e89b-12d3-a456-426614174000",  # Замените на реальный UUID
                "customer_email": "test@example.com",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }

            headers = {
                "Authorization": "Bearer YOUR_TEST_TOKEN",  # Замените на реальный токен
                "Content-Type": "application/json"
            }

            response = await client.post(
                "http://localhost:8000/stripe/create-checkout-session/",
                json=test_data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ API endpoint working!")
                print(f"Response: {result}")
                return result
            else:
                print(f"❌ API endpoint failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None

    except Exception as e:
        print(f"❌ API test failed: {e}")
        return None


async def main():
    print("🧪 Testing Stripe Integration...")
    print("=" * 50)

    # Проверка переменных окружения
    if not os.getenv("STRIPE_SECRET_KEY"):
        print("❌ STRIPE_SECRET_KEY not found in environment variables")
        return

    print(f"🔑 Using Stripe key: {os.getenv('STRIPE_SECRET_KEY')[:12]}...")
    print()

    # Тест 1: Подключение к Stripe
    print("1. Testing Stripe connection...")
    await test_stripe_connection()
    print()

    # Тест 2: Создание checkout session
    print("2. Testing checkout session creation...")
    session = await test_checkout_session()
    print()

    # Тест 3: API эндпоинт (опционально)
    print("3. Testing API endpoint (optional)...")
    print("⚠️  Make sure your server is running on localhost:8000")
    print("⚠️  Update subscription_id and auth token in the script")
    # await test_api_endpoint()

    print("=" * 50)
    print("🏁 Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
