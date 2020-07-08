from endorsity.celery import app

from accounts.models import Brand


@app.task
def end_subscription(user_pk):
    print(user_pk)
    brand = Brand.objects.get(user__pk=user_pk)
    brand.is_subscription_active = False
    brand.save()
