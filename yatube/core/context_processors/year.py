from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    current_date = date.today()
    current_date_string = current_date.strftime('%Y')
    return {'year': int(current_date_string)}
