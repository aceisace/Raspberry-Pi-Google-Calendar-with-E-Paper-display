#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Calendar module for Inky-Calendar Project
Copyright by aceisace
"""
from inkycal.modules.template import inkycal_module
from inkycal.custom import *

import calendar as cal
import arrow

filename = os.path.basename(__file__).split('.py')[0]
logger = logging.getLogger(filename)


class Calendar(inkycal_module):
  """Calendar class
  Create monthly calendar and show events from given icalendars
  """

  name = "Calendar - Show monthly calendar with events from iCalendars"

  optional = {

    "week_starts_on" : {
      "label":"When does your week start? (default=Monday)",
      "options": ["Monday", "Sunday"],
      "default": "Monday"
      },

    "show_events" : {
      "label":"Show parsed events? (default = True)",
      "options": [True, False],
      "default": True
      },

    "ical_urls" : {
      "label":"iCalendar URL/s, separate multiple ones with a comma, e.g. http://example.com/calendar or with authentication: http://username:password@example.com/calendar. Please do not enter username/password in the WebUI. Add them afterwards in the json file manually.",
      },

    "ical_files" : {
      "label":"iCalendar filepaths, separated with a comma",
      },

    "date_format":{
      "label":"Use an arrow-supported token for custom date formatting "+
      "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. D MMM",
      "default": "D MMM",
      },

    "time_format":{
      "label":"Use an arrow-supported token for custom time formatting "+
      "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. HH:mm",
      "default": "HH:mm"
      },

    }

  def __init__(self, config):
    """Initialize inkycal_calendar module"""

    super().__init__(config)
    config = config['config']

    # optional parameters
    self.weekstart = config['week_starts_on']
    self.show_events = config['show_events']
    self.date_format = config["date_format"]
    self.time_format = config['time_format']
    self.language = config['language']

    if config['ical_urls'] and isinstance(config['ical_urls'], str):
      self.ical_urls = config['ical_urls'].split(',')
    else:
      self.ical_urls = config['ical_urls']

    if config['ical_files'] and isinstance(config['ical_files'], str):
      self.ical_files = config['ical_files'].split(',')
    else:
      self.ical_files = config['ical_files']

    # additional configuration
    self.timezone = get_system_tz()
    self.num_font = ImageFont.truetype(
      fonts['NotoSans-SemiCondensed'], size = self.fontsize)

    # give an OK message
    print(f'{filename} loaded')

  def generate_image(self):
    """Generate image for this module"""

    # Define new image size with respect to padding
    im_width = int(self.width - (2 * self.padding_left))
    im_height = int(self.height - (2 * self.padding_top))
    im_size = im_width, im_height

    logger.info(f'Image size: {im_size}')

    # Create an image for black pixels and one for coloured pixels
    im_black = Image.new('RGB', size = im_size, color = 'white')
    im_colour = Image.new('RGB', size = im_size, color = 'white')

    # Allocate space for month-names, weekdays etc.
    month_name_height = int(im_height * 0.10)
    weekdays_height = int(self.font.getsize('hg')[1] * 1.25)
    logger.debug(f"month_name_height: {month_name_height}")
    logger.debug(f"weekdays_height: {weekdays_height}")

    if self.show_events == True:
      logger.debug("Allocating space for events")
      calendar_height = int(im_height * 0.6)
      events_height = im_height - month_name_height - weekdays_height - calendar_height
      logger.debug(f'calendar-section size: {im_width} x {calendar_height} px')
      logger.debug(f'events-section size: {im_width} x {events_height} px')
    else:
      logger.debug("Not allocating space for events")
      calendar_height = im_height - month_name_height - weekdays_height
      logger.debug(f'calendar-section size: {im_width} x {calendar_height} px')

    # Create a 7x6 grid and calculate icon sizes
    calendar_rows, calendar_cols = 6, 7
    icon_width = im_width // calendar_cols
    icon_height = calendar_height // calendar_rows
    logger.debug(f"icon_size: {icon_width}x{icon_height}px")

    # Calculate spacings for calendar area
    x_spacing_calendar = int((im_width % calendar_cols) / 2)
    y_spacing_calendar = int((im_height % calendar_rows) / 2)

    logger.debug(f"x_spacing_calendar: {x_spacing_calendar}")
    logger.debug(f"y_spacing_calendar :{y_spacing_calendar}")

    # Calculate positions for days of month
    grid_start_y = (month_name_height + weekdays_height + y_spacing_calendar)
    grid_start_x = x_spacing_calendar

    grid_coordinates = [(grid_start_x + icon_width*x, grid_start_y + icon_height*y)
            for y in range(calendar_rows) for x in range(calendar_cols)]

    weekday_pos = [(grid_start_x + icon_width*_, month_name_height) for _ in
                   range(calendar_cols)]

    now = arrow.now(tz = self.timezone)

    # Set weekstart of calendar to specified weekstart
    if self.weekstart == "Monday":
      cal.setfirstweekday(cal.MONDAY)
      weekstart = now.shift(days = - now.weekday())
    else:
      cal.setfirstweekday(cal.SUNDAY)
      weekstart = now.shift(days = - now.isoweekday())

    # Write the name of current month
    write(im_black, (0,0),(im_width, month_name_height),
      str(now.format('MMMM',locale=self.language)), font = self.font,
      autofit = True)

    # Set up weeknames in local language and add to main section
    weekday_names = [weekstart.shift(days=+_).format('ddd',locale=self.language)
      for _ in range(7)]
    logger.debug(f'weekday names: {weekday_names}')

    for _ in range(len(weekday_pos)):
      write(
        im_black,
        weekday_pos[_],
        (icon_width, weekdays_height),
        weekday_names[_],
        font = self.font,
        autofit = True,
        fill_height=1.0
        )

    # Create a calendar template and flatten (remove nestings)
    flatten = lambda z: [x for y in z for x in y]
    calendar_flat = flatten(cal.monthcalendar(now.year, now.month))
    #logger.debug(f" calendar_flat: {calendar_flat}")

    # Map days of month to co-ordinates of grid -> 3: (row2_x,col3_y)
    grid = {}
    for i in calendar_flat:
      if i != 0:
        grid[i] = grid_coordinates[calendar_flat.index(i)]
    #logger.debug(f"grid:{grid}")

    # remove zeros from calendar since they are not required
    calendar_flat = [num for num in calendar_flat if num != 0]

    # Add the numbers on the correct positions
    for number in calendar_flat:
      if number != int(now.day):
        write(im_black, grid[number], (icon_width, icon_height),
          str(number), font = self.num_font, fill_height = 0.5, fill_width=0.5)

    # Draw a red/black circle with the current day of month in white
    icon = Image.new('RGBA', (icon_width, icon_height))
    current_day_pos = grid[int(now.day)]
    x_circle,y_circle = int(icon_width/2), int(icon_height/2)
    radius = int(icon_width * 0.2)
    ImageDraw.Draw(icon).ellipse(
      (x_circle-radius, y_circle-radius, x_circle+radius, y_circle+radius),
      fill= 'black', outline=None)
    write(icon, (0,0), (icon_width, icon_height), str(now.day),
          font=self.num_font, fill_height = 0.5, colour='white')
    im_colour.paste(icon, current_day_pos, icon)


    # If events should be loaded and shown...
    if self.show_events == True:

      # If this month requires 5 instead of 6 rows, increase event section height
      if len(cal.monthcalendar(now.year, now.month)) == 5:
        events_height += icon_height

      # import the ical-parser
      from inkycal.modules.ical_parser import iCalendar

      # find out how many lines can fit at max in the event section
      line_spacing = 0
      max_event_lines = events_height // (self.font.getsize('hg')[1] +
                                          line_spacing)

      # generate list of coordinates for each line
      events_offset = im_height - events_height
      event_lines = [(0, events_offset + int(events_height/max_event_lines*_))
                     for _ in range(max_event_lines)]

      #logger.debug(f"event_lines {event_lines}")


      # timeline for filtering events within this month
      month_start = arrow.get(now.floor('month'))
      month_end = arrow.get(now.ceil('month'))

      # fetch events from given icalendars
      self.ical = iCalendar()
      parser = self.ical

      if self.ical_urls:
        parser.load_url(self.ical_urls)
      if self.ical_files:
        parser.load_from_file(self.ical_files)

      # Filter events for full month (even past ones) for drawing event icons
      month_events = parser.get_events(month_start, month_end, self.timezone)
      parser.sort()
      self.month_events = month_events

      # find out on which days of this month events are taking place
      days_with_events = [int(events['begin'].format('D')) for events in
                          month_events]

      # remove duplicates (more than one event in a single day)
      list(set(days_with_events)).sort()
      self._days_with_events = days_with_events

      # Draw a border with specified parameters around days with events
      for days in days_with_events:
        draw_border(
          im_colour,
          grid[days],
          (icon_width, icon_height),
          radius = 6,
          thickness= 1,
          shrinkage = (0.4, 0.2)
          )

      # Filter upcoming events until 4 weeks in the future
      parser.clear_events()
      upcoming_events = parser.get_events(now, now.shift(weeks=4),
                                          self.timezone)
      self._upcoming_events = upcoming_events

      # delete events which won't be able to fit (more events than lines)
      upcoming_events[:max_event_lines]


      # Check if any events were found in the given timerange
      if upcoming_events:

        # Find out how much space (width) the date format requires
        lang = self.language

        date_width = int(max([self.font.getsize(
          events['begin'].format(self.date_format,locale=lang))[0]
          for events in upcoming_events]) * 1.1)

        time_width = int(max([self.font.getsize(
          events['begin'].format(self.time_format, locale=lang))[0]
          for events in upcoming_events]) * 1.1)

        line_height = self.font.getsize('hg')[1] + line_spacing

        event_width_s = im_width - date_width - time_width
        event_width_l = im_width - date_width

        # Display upcoming events below calendar
        tomorrow = now.shift(days=1).floor('day')
        in_two_days = now.shift(days=2).floor('day')

        cursor = 0
        for event in upcoming_events:
          if cursor < len(event_lines):
            name = event['title']
            date = event['begin'].format(self.date_format, locale=lang)
            time = event['begin'].format(self.time_format, locale=lang)
            #logger.debug(f"name:{name}   date:{date} time:{time}")

            if now < event['end']:
              write(im_colour, event_lines[cursor], (date_width, line_height),
                    date, font=self.font, alignment = 'left')

              # Check if event is all day
              if parser.all_day(event) == True:
                write(im_black, (date_width, event_lines[cursor][1]),
                    (event_width_l, line_height), name, font=self.font,
                    alignment = 'left')
              else:
                write(im_black, (date_width, event_lines[cursor][1]),
                    (time_width, line_height), time, font=self.font,
                    alignment = 'left')

                write(im_black, (date_width+time_width,event_lines[cursor][1]),
                    (event_width_s, line_height), name, font=self.font,
                    alignment = 'left')
              cursor += 1
      else:
        symbol = '- '
        while self.font.getsize(symbol)[0] < im_width*0.9:
          symbol += ' -'
        write(im_black, event_lines[0],
              (im_width, self.font.getsize(symbol)[1]), symbol,
              font = self.font)

    # return the images ready for the display
    return im_black, im_colour

if __name__ == '__main__':
  print(f'running {filename} in standalone mode')
