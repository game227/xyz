"""Obuna tariflari — onlayn to‘lov yo‘q; faqat ko‘rsatish va so‘rov uchun."""

SUBSCRIPTION_PLANS = (
    {
        'days': 30,
        'title': '1 oy',
        'price_label': '149 000 so‘m',
        'blurb': 'Barcha darslar, video va testlar',
        'popular': False,
    },
    {
        'days': 90,
        'title': '3 oy',
        'price_label': '349 000 so‘m',
        'blurb': 'Eng qulay — 3 oy to‘liq kirish',
        'popular': True,
    },
    {
        'days': 180,
        'title': '6 oy',
        'price_label': '599 000 so‘m',
        'blurb': 'Imtihongacha to‘liq tayyorgarlik',
        'popular': False,
    },
)

PLAN_DAYS_CHOICES = [(p['days'], p['title']) for p in SUBSCRIPTION_PLANS]
