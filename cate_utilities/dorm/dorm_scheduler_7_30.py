import datetime, random, csv, math, collections, sys

def make_dates(start_date, end_date, skip_dates = []):
    """
    expects:
        start_date is a date string in mm/dd/yyyy format
        end_date is a date string in  mm/dd/yyyy format
        skip_dates is a list of 'mm/dd/yyyy' strings and/or 'mm/dd/yyyy - mm/dd/yyyy'
    returns:
        a list of datetime.date objects
    """
    start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y').date()
    end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y').date()
    dates = []
    date = start_date
    while date <= end_date:
        dates.append(date)
        date += datetime.timedelta(days=1)

    for skip_date in skip_dates:
        if '-' in skip_date:
            i = skip_date.index('-')
            mydates = make_dates(skip_date[:i].strip(), skip_date[i+1:].strip())
            for date in mydates:
                if date in dates:
                    dates.remove(date)
        else:
            date = datetime.datetime.strptime(skip_date, '%m/%d/%Y').date()
            if date in dates:
                dates.remove(date)
    return dates#make a list of dates

def make_weekend_lists(dorm):
    dates = [date for date in dorm.on_duty.keys() if dorm.on_duty[date] == None]
    weekends = ['Friday', 'Saturday']
    #count fridays and saturdays
    count_weekends = {}
    for day in weekends:
        count_weekends[day] = len([date for date in dorm.on_duty.keys()
                                   if date.strftime('%A') == day])

    #fill out weekend list with right number of each faculty member's name
    partials = [fac.name for fac in dorm.faculty if fac.load == 'partial']
    fulls = [fac.name for fac in dorm.faculty if fac.load == 'full']
    weekend_list = {}
    for day in weekends:
        weekend_list[day] = []
        #round up to figure out # of duties -- we'll trim fairly later
        num_duties = int(math.ceil(count_weekends[day]/float(len(dorm.faculty))))
        for fac in dorm.faculty:
            for i in range(num_duties):
                weekend_list[day].append(fac.name)

    #trim lists, removing residential faculty first but doing it as balanced as possible
    trim_list = partials + fulls
    for day in weekends:
        overage = len(weekend_list[day]) - count_weekends[day]
        for i in range(overage):
            if len(trim_list) == 0:
                trim_list = partials + fulls
            name = trim_list[0]
            trim_list = trim_list[1:]
            weekend_list[day].remove(name)

    #remove responsibility for days already assigned (designed mainly for the dormhead)
    for date in [date for date in dorm.on_duty.keys() if dorm.on_duty[date] != None]:
        for day in weekends:
            if date.strftime('%A') == day:
                weekend_list[day].remove(dorm.on_duty[date])

    # count the weekend days to be assigned
    for day in weekends:
        count_weekends[day] = len([ date for date in dorm.on_duty.keys()
                                   if date.strftime('%A') == day
                                    and dorm.on_duty[date] == None ])

    #make replacement list
    nweekends = len(weekend_list['Friday']) + len(weekend_list['Saturday'])
    fulls = []
    fulls = [fac.name for fac in dorm.faculty if fac.load == 'full']
    weekend_replacement_list = []
    while len(weekend_replacement_list) < nweekends:
        for name in fulls:
            weekend_replacement_list.append(name)
    weekend_replacement_list = weekend_replacement_list[:nweekends]

    return weekend_list, weekend_replacement_list


class Faculty():
    def __init__(self, name, role, dorm, load = None):
        self.name = name
        self.role = role
        if load == None:
            if role == 'adjunct':
                self.load = 'partial'
            else:
                self.load = 'full'
        elif load in ['partial', 'full']:
            self.load = load
        else:
            raise ValueError('%s not a valid load' % load)

        self.unavailable_dates = []
        self.unavailable_dow = []
        self.on_duty = []
        self.dorm = dorm

    def set_unavailable_date(self, date):
        self.unavailable_dates.append(date)

    def set_unavailable_dow(self, dow):
        self.unavailable_dow.append(dow)

    def set_on_duty(self, date):
        if date in self.unavailable_dates or date.strftime('%A') in self.unavailable_dow:
            raise Exception('Unavailable')
        else:
            self.on_duty.append(date)

    def set_off_duty(self, date):
        if date in self.on_duty:
            self.on_duty.remove(date)

    def get_worst_day(self, dates):
        worst_count = 0
        worst_day = None
        self.on_duty.sort()
        for date in self.on_duty:
            if date not in dates or date.strftime('%A') in weekends:
                continue
            lower_date = date - datetime.timedelta(days=3)
            upper_date = date + datetime.timedelta(days=3)
            count = 0
            for test_date in self.on_duty:
                if lower_date <= test_date <= upper_date:
                    count += 1
            if count >= worst_count:
                worst_count = count
                worst_day = date
        return worst_day


class Dorm():
    def __init__(self, name):

        self.name = name
        #define a list of faculty instances
        self.faculty = []
        #define a dictionary that connects dates to names (this would be better as instances)
        self.on_duty = {}
        #define a dictionary to connect names to Faculty instances
        self.fac_instance = {}

        #initialize dates
        self.trimester_breaks = [datetime.date(2014, 11, 22), datetime.date(2015, 2, 28)]
        vacation_list = ['9/5/2014-9/13/2014', '11/23/2014-11/30/2014',
                         '12/20/2014-1/4/2015', '3/1/2015-3/14/2015']
        dates = make_dates('8/25/2014', '5/29/2015', vacation_list)
        #initialize duties to None
        for date in dates:
            self.set_on_duty(date, None)
        head_dates_str = ['8/25/2014', '8/26/2014', '11/22/2014', '12/1/2014', '12/19/2014',
                      '1/5/2015', '2/28/2015', '3/15/2015', '5/30/2015']
        self.head_dates = []
        for date in head_dates_str:
            self.head_dates.append(datetime.datetime.strptime(date, '%m/%d/%Y').date())

    def add_faculty(self, name, role = 'adjunct', load = None):
        roles = ['adjunct', 'residential', 'head']
        if role not in roles:
            raise Exception('Role: %s not in roles' % role)
        self.fac_instance[name] = Faculty(name, role, self, load)
        self.faculty.append(self.fac_instance[name])
        if role == 'head':
            for date in self.head_dates:
                self.set_on_duty(date, name)

    def get_faculty_names(self):
        names = []
        for fac in self.faculty:
            names.append(fac.name)
        return names

    def get_faculty_names_by_role(self, role):
        names = []
        for fac in self.faculty:
            if fac.role == role:
                names.append(fac.name)
        return names

    def export_csv(self, name = None):
        filename = self.name + '_calendar.csv'
        with open(filename, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Subject', 'Start Date', 'Description'])
            for date in sorted(self.on_duty.keys()):
                if name == None or name == self.on_duty[date]:
                    csvwriter.writerow([self.name + ' ' + self.on_duty[date], date.strftime('%m/%d/%Y'),
                                        date.strftime('%A')])

    def set_on_duty(self, date, name):
        #turn off old assignments
        for fac in self.faculty:
           fac.set_off_duty(date)
        if name != None:
            #turn on new assignment in the faculty member itself
            try:
                self.fac_instance[name].set_on_duty(date)
            except:
                raise Exception('date unavailable')
        #turn on new assignment here
        self.on_duty[date] = name

    def calculate_shares(self):
        num_partial = 0
        num_full = 0
        for fac in self.faculty:
            if fac.load == 'partial':
                num_partial += 1
            elif fac.load == 'full':
                num_full += 1
            else:
                raise ValueError('Invalid name for load: ', fac.load)

        num_adjunct =len(self.get_faculty_names_by_role('adjunct'))
        num_res = len(self.get_faculty_names_by_role('residential')) + 1
        share = {}
        share['partial'] = 1./7
        share['full'] = (1. - share['partial']*num_partial)/num_full
        return share

    def get_adjuncts(self):
        adjuncts = [fac.name for fac in self.faculty if fac.role == 'adjunct']
        return adjuncts

    def get_duty_counts(self):
        count = {}
        for fac in self.faculty:
            count[fac.name] = {}
            count[fac.name]['weekdays'] = 0
            count[fac.name]['Friday'] = 0
            count[fac.name]['Saturday'] = 0
            count[fac.name]['total'] = 0
        for date in self.on_duty.keys():
            name = self.on_duty[date]
            count[name]['total'] += 1
            dow = date.strftime('%A')
            if dow in weekdays:
                count[name]['weekdays'] += 1
            else: #weekend
                count[name][dow] += 1
        print 'Name', 'total', 'Weekdays', 'Fridays', 'Saturdays'
        for fac in self.faculty:
            print fac.name, count[fac.name]['total'],  count[fac.name]['weekdays'], \
                count[fac.name]['Friday'], count[fac.name]['Saturday']

    def assign_weekday_defaults(self, input_assignments = {}):
        success = False
        while not success:
            success = True
            default_dict = input_assignments.copy()
            faculty_tba = self.faculty[:]
            for name in default_dict.values():
                faculty_tba.remove(self.fac_instance[name])
            for day in weekdays:
                if day not in default_dict.keys():
                    def_fac = random.choice(faculty_tba)
                    faculty_tba.remove(def_fac)
                    default_dict[day]=def_fac.name
            for day in weekdays:
                if day in self.fac_instance[default_dict[day]].unavailable_dow:
                    success = False
        return default_dict

    def assign_weekends(self):
        dates = sorted([date for date in self.on_duty.keys() if self.on_duty[date] == None])
        #get lists of weekend faculty and their weekday replacements
        weekend_list, weekend_replacement_list = make_weekend_lists(self)

        friday_list = [fac.name for fac in self.faculty]
        saturday_list = [fac.name for fac in self.faculty][::-1]
        print 'friday, saturday', friday_list, saturday_list

        for date in dates:
            if date.strftime('%A') == 'Friday':
                success = False
                index = 0
                while not success:
                    success = True
                    name = friday_list[index]
                    try:
                        self.set_on_duty(date, name)
                    except:
                        success = False
                        index += 1
                friday_list.remove(name)
                friday_list.append(name)
                print 'friday', name, friday_list
            if date.strftime('%A') == 'Saturday':
                success = False
                index = 0
                while not success:
                    name = saturday_list[index]
                    friday = date - datetime.timedelta(days = 1)
                    if name == self.on_duty[friday]:
                        index += 1
                        continue
                    success = True
                    try:
                        self.set_on_duty(date, name)
                    except:
                        success = False
                        index += 1
                saturday_list.remove(name)
                saturday_list.append(name)
                print 'saturday', name, saturday_list

        """
        #assign weekends
        for date in dates:
            for day in weekends:
                if date.strftime('%A') == day:
                    success = False
                    iter = 0
                    while not success:
                        success = True
                        #print date, date.strftime('%A'), iter, weekend_list[day]
                        try:
                            if len(weekend_list[day]) == 0:
                                print 'I\'m out of names!', day
                                name = random.choice(self.get_faculty_names())
                            else:
                                name = random.choice(weekend_list[day])
                            self.set_on_duty(date, name)
                        except:
                            iter += 1
                            success = False
                            if iter == 100:
                                print 'I got stuck assigning ', day, date
                                print 'I\'m assigning a random faculty member.'
                                newsuccess = False
                                while not newsuccess:
                                    name = random.choice(self.get_faculty_names())
                                    newsuccess = True
                                    try:
                                        self.set_on_duty(date, name)
                                    except:
                                        newsuccess = False
                                success = True
                    if name in weekend_list[day]:
                        weekend_list[day].remove(name)

        """
        #now go through weekends again and replace weekday assignments
        #print 'balancing weekends with weekdays'
        partials = []
        for fac in self.faculty:
            if fac.load == 'partial':
                partials.append(fac.name)

        for date in dates:
            name = self.on_duty[date]
            if date.strftime('%A') in weekends and name in partials:
                #make a list of dates to check.
                if date.strftime('%A') == 'Friday' :
                    other_name = self.on_duty[date + datetime.timedelta(days = 1)]
                    dates_to_check = [date + datetime.timedelta(days = 2)]
                    for i in range(1,5):
                        dates_to_check.append(date - datetime.timedelta(days = i))
                else: #Saturday
                    other_name = self.on_duty[date - datetime.timedelta(days = 1)]
                    dates_to_check = [date + datetime.timedelta(days = 1)]
                    for i in range(2,6):
                        dates_to_check.append(date - datetime.timedelta(days = i))
                #find nearby dates served by the adjunct faculty
                nearby_dates = []
                for mydate in dates_to_check:
                    try:  # need this in case date is not in list of dates
                        if self.on_duty[mydate] == name:
                            nearby_dates.append(mydate)
                    except:
                        pass
                #if there are any, replace them with dorm faculty
                if len(nearby_dates) > 0:
                    newdate = random.choice(nearby_dates)
                    short_list = [x for x in weekend_replacement_list if x != other_name]
                    if len(short_list) > 0:
                        success = False
                        iter = 0
                        while not success:
                            success = True
                            try:
                                newname = random.choice(short_list)
                                self.set_on_duty(newdate, newname)
                                weekend_replacement_list.remove(newname)
                            except:
                                success = False
                                iter += 1
                                if iter == 100:
                                    print 'Trouble.  Oh, trouble move from me.'
                                    sys.exit(-1)

    def rebalance_weekdays(self):
        weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        def calculate_overload():
            share = self.calculate_shares()
            overload = {}
            for fac in self.faculty:
                overload[fac.name] = len(fac.on_duty) - share[fac.load]*len(self.on_duty)
            #sort list in order of increasing overload, see http://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
            overload_list = sorted(overload, key=overload.get)
            biggest_load_diff = overload[overload_list[-1]] - overload[overload_list[0]]
            return overload_list[-1], overload_list[0], biggest_load_diff
        most_loaded, least_loaded, load_diff = calculate_overload()
        while load_diff > 1.:
            #give the lowest-load person the biggest load's worst day
            dates = [date for date in self.on_duty.keys()
                     if date not in self.head_dates
                and date.strftime('%A') in weekdays]
            success = False
            while not success:
                success = True
                worst_day = self.fac_instance[most_loaded].get_worst_day(dates)
                try:
                    self.set_on_duty(worst_day, least_loaded)
                except:
                    success = False
                    dates.remove(worst_day)
            most_loaded, least_loaded, load_diff = calculate_overload()

    def assign_weekdays(self):
        #assign default weekdays
        weekday_defaults = {}
        for i in range(3):
            weekday_defaults[i] = self.assign_weekday_defaults()

        for date in [date for date in self.on_duty.keys() if self.on_duty[date] == None and
                date.strftime('%A') in weekdays]:
            dow = date.strftime('%A')
            if date < self.trimester_breaks[0]:
                trimester = 0
            elif date < self.trimester_breaks[1]:
                trimester = 1
            else:
                trimester = 2
            name = weekday_defaults[trimester][dow]
            success = False
            while not success:
                success = True
                try:
                    self.set_on_duty(date, name)
                except:
                    faculty = random.choice(self.faculty).name
                    success = False

    def make_schedule(self):
        self.assign_weekdays()
        self.assign_weekends()
        self.rebalance_weekdays()

weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
weekends = ['Friday', 'Saturday']

if __name__ == '__main__':
#    random.seed(128)
    #initiate the dorm and the faculty
    chw = Dorm('CHW')
    chw.add_faculty('Walter', 'adjunct')
    chw.add_faculty('Joshua', 'head')
    chw.add_faculty('Jamie', 'residential')
    chw.add_faculty('Donny', 'adjunct')
    chw.add_faculty('TheDude', 'residential')

    #for date in make_dates('9/1/2014', '9/30/2014'):
    #    chw.fac_instance['TheDude'].set_unavailable_date(date)

    chw.make_schedule()
    chw.get_duty_counts()



