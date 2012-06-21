from django.test import TestCase
from eventtools.tests._inject_app import TestCaseWithApp as AppTestCase
from eventtools.tests.eventtools_testapp.models import *
from eventtools.tests._fixture import fixture
from datetime import date, time, datetime, timedelta
from eventtools.tests._fixture import bigfixture, reload_films
from eventtools.utils import dateranges

class TestEvents(AppTestCase):

    def setUp(self):
        super(TestEvents, self).setUp()
        fixture(self)

    def test_creation(self):

        """
        When you create an TestEventModel,
        you need to create an ExampleOccurrence class with a field 'event' that FKs to event.
        
        TestOccurrences are sorted by start (then end) by default.

        """
        self.assertTrue(hasattr(ExampleEvent, 'occurrences'))
        self.assertTrue(hasattr(ExampleOccurrence, 'event'))
        
        #test sorting
        occs = ExampleOccurrence.objects.all()
        x = occs[0].start
        for o in occs:
            self.assertTrue(o.start >= x)
            x= o.start

    def test_occurrence_relation(self):
        """
        You can query the occurrences for a single event by date(datetime) range etc.
           e.occurrences.filter(status='cancelled')
           e.occurrences.all().between(dt1, dt2)
        """
        talks = self.talk.occurrences.all()
        self.ae(len(talks), 3)

        talks = self.talk.occurrences.filter(status='cancelled')
        self.ae(len(talks), 1)

        #day range
        talks = self.talk.occurrences.between(self.day1, self.day2)
        self.ae(len(talks), 3)
    
        #before and after
        talks = self.talk.occurrences.before(self.day1)
        self.ae(len(talks), 2)
        talks = self.talk.occurrences.after(self.day2)
        self.ae(len(talks), 1)

        #one day is allowed
        talks1 = self.talk.occurrences.on(self.day1)
        self.ae(len(talks1), 2)
        # and it's the same as passing the same day into the range.
        talks2 = self.talk.occurrences.between(self.day1, self.day1)
        self.ae(list(talks1), list(talks2))

        #combining queries
        talks = self.talk.occurrences.filter(status='cancelled').between(self.day1, self.day2)
        self.ae(len(talks), 1)
        
        # hour range
        morningstart = datetime.combine(self.day1, time.min)
        morningend = datetime.combine(self.day1, time(12,00))
        talks = self.talk.occurrences.between(morningstart, morningend)
        self.ae(len(talks), 1)
        
    def test_occurrences_from_events(self):
        """
        You can query occurrences for an event queryset, including by date range etc.
        
        TODO: start queries are covered in tests; ends and entirely queries are not.
        
        You can get the opening and closing occurrence for an event:
        
        """
        all_occs = ExampleEvent.eventobjects.occurrences()
        self.ae(list(all_occs), list(ExampleOccurrence.objects.all()))

        #opening and closing
        self.ae(self.performance.opening_occurrence(), self.performance_evening)
        self.ae(self.performance.closing_occurrence(), self.performance_day_after_tomorrow)

    # The bigfixture takes ages.
    # def test_advanced_queries(self):
    #     """
    #     There are shortcut occurrence queries, which define date range relative to the current day.
    #     
    #     Weeks can start on sunday (6), monday (0), etc. Weekends can be any set of days (some sites include fridays). These are defined in settings.
    #     """
    #     
    #     #create a huge fixture of occurrences for event self.pe
    #     bigfixture(self)
    #     
    #     num_per_day = 5 #how many events we generate each day
    #             
    #     peo = self.pe.occurrences
    #     
    #     #forthcoming and recent
    #     forthcoming = peo.forthcoming()
    #     recent = peo.recent()
    # 
    #     # self.ae(recent.count(), 4696)
    #     # self.ae(forthcoming.count(), 1514)
    #     
    #     dtnow = datetime.now()
    #     
    #     for o in forthcoming:
    #         self.assertTrue(o.start > dtnow)
    # 
    #     for o in recent:
    #         self.assertTrue(o.end < dtnow)
    # 
    #     on = peo.starts_on(self.todaynow)
    #     # 5 events * 5 or 6 ranges
    #     if dateranges.is_weekend(self.todaynow):
    #         self.ae(on.count(), 30)
    #     else:
    #         self.ae(on.count(), 25)
    #         
    #     # test in a few days when it prob won't be the weekend
    #     on = peo.starts_on(self.todaynow+timedelta(5))
    #     # 5 events * 4 or 5 ranges (no today)
    #     if dateranges.is_weekend(self.todaynow+timedelta(5)):
    #         self.ae(on.count(), 25)
    #     else:
    #         self.ae(on.count(), 20)
    # 
    #     week = peo.starts_in_week_of(self.todaynow+timedelta(365))
    #     # in next year. Only 7 * 5 event
    #     self.ae(week.count(), 35)        

    def test_qs_occurrences(self):
        """
        You can query ExampleEvent to find only those events that are opening or closing.
        
        A closing event is defined as the last occurrence start (NOT the last occurrence end, which would be less intuitive for users)
        
        In trees of events, the latest/earliest in an occurrence's children are
        the opening/closing event.
        
        """
        
        o = ExampleEvent.eventobjects.opening_occurrences()
        o2 = [a.opening_occurrence() for a in ExampleEvent.eventobjects.all()]
        self.ae(set(o), set(o2))

        o = ExampleEvent.eventobjects.closing_occurrences()
        o2 = [a.closing_occurrence() for a in ExampleEvent.eventobjects.all()]
        self.ae(set(o), set(o2))

    def test_change_cascade(self):       
        """
        TestEvents are in an mptt tree, which indicates parents (more general) and children (more specific).
        When you save a parent event, every changed field cascades to all children events (and not to parent events).
        If the child event has a different value to the original, then the change doesn't cascade.
        """
        self.ae(self.film.get_descendant_count(), 3)
        self.ae(set(self.film.get_descendants(include_self=True)), set([self.film, self.film_with_talk, self.film_with_talk_and_popcorn, self.film_with_popcorn]))

        self.film.title = "Irish fillum night"
        self.film.save()

        # reload everything
        reload_films(self)
                
        self.ae(self.film_with_talk.title, "Irish fillum night")
        self.ae(self.film_with_talk_and_popcorn.title, "Irish fillum night")
        self.ae(self.film_with_popcorn.title, "Irish fillum night")
        
        self.film_with_talk.title = "Ireland's best films (with free talk)"
        self.film_with_talk.save()
        # reload everything
        reload_films(self)
        
        self.ae(self.film.title, "Irish fillum night")
        self.ae(self.film_with_talk_and_popcorn.title, "Ireland's best films (with free talk)")
        
        #put it all back
        self.film.title = self.film_with_talk.title = "Film Night"
        self.film.save()
        self.film_with_talk.save()
        
        # reload everything
        reload_films(self)

    def test_diffs(self):
        self.ae(unicode(self.film), u'Film Night')
        self.ae(unicode(self.film_with_talk), u'Film Night (director\'s talk)')
    """
    DONE BUT NO TESTS: When you view an event, the diff between itself and its parent is shown, or fields are highlighted, etc, see django-moderation.
    """

    def test_times_description(self):
        """
        Testing the correct formatting and logic for Event.times_description, which tries to infer a regular starting
        time from an event's occurrences.
        """
        d1 = date(2010,1,1)
        d2 = date(2010,1,2)
        t1 = time(9,00)
        t2 = time(11,00)

        e = ExampleEvent.eventobjects.create(title="event with one occurrence")
        e.occurrences.create(start=datetime.combine(d1, t1), _duration=25*60)
        self.ae(e.times_description(), "9.00am")

        e = ExampleEvent.eventobjects.create(title="event with two occurrences on the same day, with different starting times")
        e.occurrences.create(start=datetime.combine(d1, t1), _duration=25*60)
        e.occurrences.create(start=datetime.combine(d1, t2), _duration=25*60)
        self.ae(e.times_description(), "Times vary")

        e = ExampleEvent.eventobjects.create(title="event with two occurrences on two days, with similar starting times")
        e.occurrences.create(start=datetime.combine(d1, t1), _duration=25*60)
        e.occurrences.create(start=datetime.combine(d2, t1), _duration=25*60)
        self.ae(e.times_description(), "9.00am")

        e = ExampleEvent.eventobjects.create(title="event with two occurrences on two days, with different starting times")
        e.occurrences.create(start=datetime.combine(d1, t1), _duration=25*60)
        e.occurrences.create(start=datetime.combine(d2, t2), _duration=25*60)
        self.ae(e.times_description(), "Times vary")


