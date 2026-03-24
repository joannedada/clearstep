import azure.functions as func
import json
import urllib.parse
from datetime import datetime, timedelta
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route='generate-calendar-link')
def generate_calendar_link(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except Exception:
        return func.HttpResponse(json.dumps({'error': 'Invalid JSON'}),
                                 status_code=400, mimetype='application/json')

    step_text = body.get('step_text', 'Complete this step')
    time_choice = body.get('time_choice', 'tonight')
    now = datetime.utcnow()

    if time_choice == 'tonight':
        event_start = now.replace(hour=21, minute=0, second=0, microsecond=0)
        if event_start <= now:
            event_start += timedelta(days=1)
    else:
        event_start = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

    event_end = event_start + timedelta(minutes=30)
    fmt = '%Y%m%dT%H%M%SZ'
    title = f'ClearStep reminder: {step_text}'
    description = f'You asked ClearStep to remind you to: {step_text}'

    google_params = urllib.parse.urlencode({
        'action': 'TEMPLATE',
        'text': title,
        'dates': f'{event_start.strftime(fmt)}/{event_end.strftime(fmt)}',
        'details': description,
        'sf': 'true',
        'output': 'xml'
    })
    google_link = f'https://calendar.google.com/calendar/render?{google_params}'

    outlook_params = urllib.parse.urlencode({
        'path': '/calendar/action/compose',
        'rru': 'addevent',
        'startdt': event_start.isoformat() + 'Z',
        'enddt': event_end.isoformat() + 'Z',
        'subject': title,
        'body': description
    })
    outlook_link = f'https://outlook.live.com/calendar/0/action/compose?{outlook_params}'

    return func.HttpResponse(
        json.dumps({'google_link': google_link, 'outlook_link': outlook_link, 'event_title': title}),
        status_code=200,
        mimetype='application/json',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )