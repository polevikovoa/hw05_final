import datetime


def now_and_today(request):
    today = datetime.date.today()
    year = today.year
    return {'site_name': 'My awesome site', 'site_creation_date': year}