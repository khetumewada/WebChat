from datetime import datetime

from django import template
from django.utils.dateparse import parse_datetime

register = template.Library()

@register.filter
def get_other_participant(chat, user):
    # Returns the other user in a private chat.
    return chat.get_other_participant(user)

@register.filter
def get_avatar_color(user_id):
    # You also use this in common.html, so you might need a placeholder or logic here
    colors = ['#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5']
    return colors[int(user_id) % len(colors)] if user_id else '#ccc'

@register.filter
def format_message_time(value):
    if value is None:
        return ""

    # If the value is already a datetime object, use it directly
    if isinstance(value, datetime):
        return value.strftime("%b %d")

    # If it's a string, try to parse it into a datetime object
    if isinstance(value, str):
        parsed_date = parse_datetime(value)
        if parsed_date:
            return parsed_date.strftime("%b %d")

    # Fallback: return the original value if it's not a date/formattable string
    return value