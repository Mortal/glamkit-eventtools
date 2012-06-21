# You can override these settings in Django.
# Import with
# from eventtools.conf import settings
from django.conf import settings

import calendar
FIRST_DAY_OF_WEEK = calendar.MONDAY #you may prefer Saturday or Sunday.
FIRST_DAY_OF_WEEKEND = calendar.SATURDAY #you may prefer Friday
LAST_DAY_OF_WEEKEND = calendar.SUNDAY

EVENT_GET_MAP = {
    'startdate': 'startdate',
    'enddate': 'enddate',
}

OCCURRENCES_PER_PAGE = 20

ICAL_CALNAME = getattr(settings, 'SITE_NAME', 'Events list')
ICAL_CALDESC = "Events listing" #e.g. "Events listing from mysite.com"

from dateutil.relativedelta import relativedelta
DEFAULT_GENERATOR_LIMIT = relativedelta(years=1) #months=6, etc

OCCURRENCE_STATUS_CANCELLED =  ('cancelled', 'Cancelled')
OCCURRENCE_STATUS_FULLY_BOOKED = ('fully booked', 'Fully Booked')

OCCURRENCE_STATUS_CHOICES = [
   OCCURRENCE_STATUS_CANCELLED,
   OCCURRENCE_STATUS_FULLY_BOOKED,
]