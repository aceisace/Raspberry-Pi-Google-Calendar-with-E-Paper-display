#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
iCalendar (parsing) module for Inky-Calendar Project
Copyright by aceisace
"""

"""               ---info about iCalendars---
• all day events start at midnight, ending at midnight of the next day
• iCalendar saves all event timings in UTC -> need to be converted into local
  time
• Only non-all_day events or multi-day need to be converted to
  local timezone. Converting all-day events to local timezone is a problem!
"""

import arrow
from urllib.request import urlopen
import logging
import time
import os

try:
  import recurring_ical_events
except ModuleNotFoundError:
  print('recurring-ical-events library could not be found.')
  print('Please install this with: pip3 install recurring-ical-events')

try:
  from icalendar import Calendar, Event
except ModuleNotFoundError:
  print('icalendar library could not be found. Please install this with:')
  print('pip3 install icalendar')


filename = os.path.basename(__file__).split('.py')[0]
logger = logging.getLogger(filename)

class iCalendar:
  """iCalendar parsing moudule for inkycal.
  Parses events from given iCalendar URLs / paths"""

  def __init__(self):
    self.icalendars = []
    self.parsed_events = []

  def load_url(self, url, username=None, password=None):
    """Input a string or list of strings containing valid iCalendar URLs
    example: 'URL1' (single url) OR ['URL1', 'URL2'] (multiple URLs)
    add username and password to access protected files
    """

    if type(url) == list:
      if (username == None) and (password == None):
        ical = [Calendar.from_ical(str(urlopen(_).read().decode()))
                                   for _ in url]
      else:
        ical = [auth_ical(each_url, username, password) for each_url in url]
    elif type(url) == str:
      if (username == None) and (password == None):
        ical = [Calendar.from_ical(str(urlopen(url).read().decode()))]
      else:
        ical = [auth_ical(url, username, password)]
    else:
      raise Exception (f"Input: '{url}' is not a string or list!")


    def auth_ical(url, uname, passwd):
      """Authorisation helper for protected ical files"""

      # Credit to Joshka
      password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
      password_mgr.add_password(None, url, username, password)
      handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
      opener = urllib.request.build_opener(handler)
      ical = Calendar.from_ical(str(opener.open(url).read().decode()))
      return ical

    # Add the parsed icalendar/s to the self.icalendars list
    if ical: self.icalendars += ical
    logger.info('loaded iCalendars from URLs')

  def load_from_file(self, filepath):
    """Input a string or list of strings containing valid iCalendar filepaths
    example: 'path1' (single file) OR ['path1', 'path2'] (multiple files)
    returns a list of iCalendars as string (raw)
    """
    if type(filepath) == list:
      ical = [Calendar.from_ical(str(open(path).read())) for path in filepath]
    elif type(filepath) == str:
      ical = [Calendar.from_ical(str(open(filepath).read()))]
    else:
      raise Exception (f"Input: '{filepath}' is not a string or list!")

    self.icalendars += ical
    logger.info('loaded iCalendars from filepaths')

  def get_events(self, timeline_start, timeline_end, timezone=None):
    """Input an arrow (time) object for:
    * the beginning of timeline (events have to end after this time)
    * the end of the timeline (events have to begin before this time)
    * timezone if events should be formatted to local time
    Returns a list of events sorted by date
    """
    if type(timeline_start) == arrow.arrow.Arrow:
      if timezone == None:
        timezone = 'UTC'
      t_start = timeline_start
      t_end = timeline_end
    else:
      raise Exception('Please input a valid arrow (time) object!')

    # parse non-recurring events

    # Recurring events time-span has to be in this format:
    # "%Y%m%dT%H%M%SZ" (python strftime)
    fmt = lambda date: (date.year, date.month, date.day, date.hour,
                        date.minute, date.second)

    t_start_recurring = fmt(t_start)
    t_end_recurring = fmt(t_end)

    # Fetch recurring events
    recurring_events = (recurring_ical_events.of(ical).between(
                        t_start_recurring, t_end_recurring)
                        for ical in self.icalendars)

    events = (
      {
      'title': events.get('SUMMARY').lstrip(),

      'begin': arrow.get(events.get('DTSTART').dt).to(timezone) if (
        arrow.get(events.get('dtstart').dt).format('HH:mm') != '00:00')
        else arrow.get(events.get('DTSTART').dt).replace(tzinfo=timezone),

      'end':arrow.get(events.get("DTEND").dt).to(timezone) if (
        arrow.get(events.get('dtstart').dt).format('HH:mm') != '00:00')
        else arrow.get(events.get('DTEND').dt).replace(tzinfo=timezone)

      } for ical in recurring_events for events in ical)


    # if any recurring events were found, add them to parsed_events
    if events: self.parsed_events += list(events)

    # Sort events by their beginning date
    self.sort()

    return self.parsed_events

  def sort(self):
    """Sort all parsed events in order of beginning time"""
    if not self.parsed_events:
      logger.debug('no events found to be sorted')
    else:
      # sort events by date
      by_date = lambda event: event['begin']
      self.parsed_events.sort(key=by_date)


  def clear_events(self):
    """clear previously parsed events"""

    self.parsed_events = []

  @staticmethod
  def all_day(event):
    """Check if an event is an all day event.
    Returns True if event is all day, else False
    """
    if not ('end' and 'begin') in event:
      print('Events must have a starting and ending time')
      raise Exception('This event is not valid!')
    else:
      begin, end = event['begin'], event['end']
      duration = end - begin
      if (begin.format('HH:mm') == '00:00' and end.format('HH:mm') == '00:00'
          and duration.days >= 1):
        return True
      else:
        return False

  @staticmethod
  def get_system_tz():
    """Get the timezone set by the system"""

    try:
      local_tz = time.tzname[1]
    except:
      print('System timezone could not be parsed!')
      print('Please set timezone manually!. Setting timezone to None...')
      local_tz = None
    return local_tz

  def show_events(self, fmt='DD MMM YY HH:mm'):
    """print all parsed events in a more readable way
    use the format (fmt) parameter to specify the date format
    see https://arrow.readthedocs.io/en/latest/#supported-tokens
    for more info tokens
    """

    if not self.parsed_events:
      logger.debug('no events found to be shown')
    else:
      line_width = max(len(_['title']) for _ in self.parsed_events)
      for events in self.parsed_events:
        title = events['title']
        begin, end = events['begin'].format(fmt), events['end'].format(fmt)
        print('{0} {1} | {2} | {3}'.format(
          title, ' ' * (line_width - len(title)), begin, end))


if __name__ == '__main__':
  print(f'running {filename} in standalone mode')
