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

class Faculty():
    def __init__(self, name, role, dorm, load = None, family = None):
        self.name = name
        self.role = role
        self.family = family
        if load == None:
            if role == 'adjunct':
                self.load = 'partial'
            elif role == 'hospital':
                self.load = None
            else:
                self.load = 'full'
        elif load in ['partial', 'full']:
            self.load = load
        elif load == None:
            self.load = None
        else:
            raise ValueError('%s not a valid load' % load)

        self.unavailable_dates = []
        self.unavailable_dow = []
        self.on_duty = []
        self.dorm = dorm

    def get_duty_dates(self, type = 'dorm'):
        if type.lower() == 'dorm':
            dates = sorted([date for date in self.dorm.on_duty.keys() if self.dorm.on_duty[date] == self.name])
        elif type.lower() == 'h1':
            dates = sorted([date for date in self.dorm.h1.keys() if self.dorm.h1[date] == self.name])
        elif type.lower() == 'h2':
            dates = sorted([date for date in self.dorm.h2.keys() if self.dorm.h2[date] == self.name])
        else:
            raise ValueError('Faculty.get_duty_dates:  type not valid', type)
        return dates

    def set_unavailable_date(self, date):
        self.unavailable_dates.append(date)

    def set_unavailable_dow(self, dow):
        self.unavailable_dow.append(dow)

    def set_on_duty(self, date):
        if date in self.unavailable_dates or date.strftime('%A') in self.unavailable_dow:
            raise Exception('Unavailable')
        else:
            self.on_duty.append(date)

    def get_worst_day(self, dates):
        worst_count = 0
        worst_day = None
        for date in self.get_duty_dates('dorm'):
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

        #define a roster of faculty responsible for hospital runs
        self.hr_faculty = []
        self.h1 = {}
        self.h2 = {}


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

        self.weekday_presets = {}
        for i in range(3):
            self.weekday_presets[i] = {}

    def set_hospital_run_dates(self, start_date, end_date):
        new_dates = make_dates(start_date, end_date)
        for date in new_dates:
            self.h1[date] = None
            self.h2[date] = None

    def set_hospital_runs(self):
        #build rotating list of faculty, starting with non-residential faculty (sorry)
        h1_list = []
        for fac in self.hr_faculty:
            if fac.role == 'hospital':
                h1_list.append(fac)
        for fac in self.hr_faculty:
            if fac.role == 'adjunct':
                h1_list.append(fac)
        for fac in self.hr_faculty:
            if fac.role in ['residential', 'head']:
                h1_list.append(fac)
        h2_list = h1_list[:]
        max_duties = float(len(self.h1))/len(self.hr_faculty)
        def h1_assignment_error(hardness = 'hard'):
            if hardness == 'hard':
                return (date in fac.unavailable_dates
                    or dow in fac.unavailable_dow
                    or fac.name == self.on_duty[date]
                    or (previous_day in self.h1 and self.h1[previous_day] == fac.name)
                    or fac.family == self.on_duty[date]
                    or fac.family == self.h2[date]
                )
            else:
                return (date in fac.unavailable_dates
                    or dow in fac.unavailable_dow
                    or fac.name == self.on_duty[date]
                    or fac.family == self.on_duty[date]
                )


        def h2_assignment_error(hardness = 'hard'):
            return (date in fac.unavailable_dates
                    or dow in fac.unavailable_dow
                    or fac.name == self.on_duty[date]
                    or fac.name == self.h1[date]
                    or fac.family == self.on_duty[date]
                    or fac.family == self.h1[date]
                )

        for date in sorted(self.h1.keys()):
            dow = date.strftime('%A')
            previous_day =date - datetime.timedelta(days = 1)
            #Assign hospital run #1
            index = 0
            while self.h1[date] == None:
                fac = h1_list[index]
                if h1_assignment_error():
                    index += 1
                else:
                    self.h1[date] = fac.name
            if len(fac.get_duty_dates('h1')) >= max_duties:
                h1_list.remove(fac)
                h1_list.append(fac)
            #Now assign hospital run #2
            index = 0
            while self.h2[date] == None:
                fac = h2_list[index]
                if h2_assignment_error():
                    index += 1
                    success = False
                else:
                    self.h2[date] = fac.name
            if len(fac.get_duty_dates('h1')) + len(fac.get_duty_dates('h2')) >= 2*max_duties:
                h2_list.remove(fac)
                h2_list.append(fac)

        # now balance
        def calculate_overload(h):
            share = self.calculate_shares()
            overload = {}
            for fac in self.hr_faculty:
                overload[fac.name] = len(fac.get_duty_dates(h)) - max_duties
            #sort list in order of increasing overload, see http://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
            overload_list = sorted(overload, key=overload.get)
            #print [fac + ':' + str(overload[fac]) for fac in overload_list]
            max_diff = overload[overload_list[-1]] - overload[overload_list[0]]
            return overload_list, max_diff, overload

        for h in ['h1', 'h2']:
            overload_list, max_diff, overload = calculate_overload(h)
            iter = 0
            while max_diff > 1.:
                iter += 1
                if iter >= 100:
                    print 'oops', h, max_diff
                    sys.exit(-1)
                overloaded = overload_list[-1]
                underloaded_index = 0
                index = 0
                date = self.fac_instance[overloaded].get_duty_dates(h)[index]
                while eval('self.' + h + '[date]') == overloaded:
                    underloaded = overload_list[underloaded_index]
                    #print h, overloaded, underloaded, max_diff, date, self.on_duty[date]
                    if underloaded == overloaded:
                        print 'exhausted all possibilities', overloaded
                        continue
                    fac = self.fac_instance[underloaded]
                    if eval(h+'_assignment_error(\'soft\')'):
                        index += 1
                        try:
                            date = self.fac_instance[overloaded].get_duty_dates(h)[index]
                        except:
                            #we've tried too many dates.  go to the next underloaded person
                            underloaded_index += 1
                            index = 0
                    else:
                        if h == 'h1':
                            self.h1[date] = underloaded
                        else:
                            self.h2[date] = underloaded
                overload_list, max_diff,  overload = calculate_overload(h)
        #    print h, overload_list, max_diff
        #    print [fac.name+':'+str(len(fac.get_duty_dates(h))) for fac in self.hr_faculty]
        #print 'date', 'on duty', 'h1', 'h2'
        #for date in sorted(self.h1.keys()):
        #    print date, self.on_duty[date], self.h1[date], self.h2[date]

    def add_faculty(self, name, role = 'adjunct', load = None, family = None):
        roles = ['adjunct', 'residential', 'head', 'hospital']
        if role not in roles:
            raise Exception('Role: %s not in roles' % role)
        self.fac_instance[name] = Faculty(name, role, self, load, family)

        #put all faculty in hospital run faculty list
        self.hr_faculty.append(self.fac_instance[name])

        #only put dorm faculty in regular faculty list
        if role != 'hospital':
            self.faculty.append(self.fac_instance[name])

        #if this is the dorm head, assign necessary dates
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

    def export_duty_to_csv(self, name = None):
        filename = self.name + '_calendar.csv'
        with open(filename, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Subject', 'Start Date', 'End Date', 'All Day Event', 'Description', 'Private'])
            for date in sorted(self.on_duty.keys()):
                if name == None or name == self.on_duty[date]:
                    csvwriter.writerow([self.name + ' ' + self.on_duty[date],
                                        date.strftime('%m/%d/%Y'),
                                        (date + datetime.timedelta(days = 1)).strftime('%m/%d/%Y'),
                                        'TRUE',
                                        '',
                                        'FALSE'])

    def export_hr_to_csv(self):
        mydict = {'H1':self.h1, 'H2':self.h2}
        for hr in mydict.keys():
            filename = self.name + '_' + hr +'_calendar.csv'
            with open(filename, 'wb') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(['Subject', 'Start Date', 'End Date', 'All Day Event', 'Description', 'Private'])
                for date in sorted(self.h1.keys()):
                    name = mydict[hr][date]
                    csvwriter.writerow([hr + ' ' + name,
                                    date.strftime('%m/%d/%Y'),
                                    (date + datetime.timedelta(days = 1)).strftime('%m/%d/%Y'),
                                    'TRUE',
                                    '',
                                    'FALSE'])

    def set_on_duty(self, date, name):
        #turn off old assignments
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

        num_weekdays = 0
        num_fridays = 0
        num_saturdays = 0
        for date in self.on_duty:
            dow = date.strftime('%A')
            if dow in weekdays:
                num_weekdays += 1
            elif dow == 'Friday':
                num_fridays += 1
            else:
                num_saturdays += 1
        num_days = num_weekdays + num_fridays + num_saturdays

        share = {}
        share['partial'] = float(num_weekdays + num_saturdays)/(num_partial + num_full)
        share['full'] = float(num_days - share['partial']*num_partial)/num_full
        return share

    def get_adjuncts(self):
        adjuncts = [fac.name for fac in self.faculty if fac.role == 'adjunct']
        return adjuncts

    def get_duty_counts(self):
        count = {}
        for fac in self.hr_faculty:
            count[fac.name] = {}
            count[fac.name]['weekdays'] = 0
            count[fac.name]['Friday'] = 0
            count[fac.name]['Saturday'] = 0
            count[fac.name]['total'] = 0
            count[fac.name]['H1'] = 0
            count[fac.name]['H2'] = 0
        for date in self.on_duty.keys():
            name = self.on_duty[date]
            count[name]['total'] += 1
            dow = date.strftime('%A')
            if dow in weekdays:
                count[name]['weekdays'] += 1
            else: #weekend
                count[name][dow] += 1
        print 'Name', 'total', 'Weekdays', 'Fridays', 'Saturdays', 'H1', 'H2'
        for fac in self.faculty:
            print fac.name, count[fac.name]['total'],  count[fac.name]['weekdays'], \
                count[fac.name]['Friday'], count[fac.name]['Saturday'], \
                len(fac.get_duty_dates('h1')), len(fac.get_duty_dates('h2'))

    def assign_weekday_defaults(self, weekday_presets = {}):
        success = False
        while not success:
            success = True
            default_dict = weekday_presets.copy()
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
        dates = sorted([date for date in self.on_duty.keys()])
        weekend_list = {}
        weekend_list['Friday'] = [fac.name for fac in self.faculty]
        weekend_list['Saturday'] = [fac.name for fac in self.faculty][::-1]

        #put the head at the end of both lists so they don't get overloaded w/ preassignments
        for fac in self.faculty:
            if fac.role == 'head':
                head = fac.name
        for day in weekends:
            weekend_list[day].remove(head)
            weekend_list[day].append(head)

        for date in dates:
            dow = date.strftime('%A')
            if dow in weekends:
                if self.on_duty[date] == None:
                    success = False
                    index = 0
                    while not success:
                        success = True
                        name = weekend_list[dow][index]
                        #make sure that no one gets friday-saturday duty
                        if dow == 'Saturday':
                            friday = date - datetime.timedelta(days = 1)
                            if name == self.on_duty[friday]:
                                index += 1
                                name = weekend_list[dow][index]
                        try:
                            self.set_on_duty(date, name)
                        except:
                            success = False
                            index += 1
                name = self.on_duty[date]
                try:
                    weekend_list[dow].remove(name)
                    weekend_list[dow].append(name)
                except:
                    print 'dow', dow
                    print 'name=', name
                    print 'list=', weekend_list[dow]
                    sys.exit(-1)

        #now go through weekends again and replace weekday assignments
        partials = []
        replacement_list = []
        for fac in self.faculty:
            if fac.load == 'partial':
                partials.append(fac.name)
            elif fac.load == 'full':
                replacement_list.append(fac.name)
            else:
                raise ValueError

        for date in dates:
            name = self.on_duty[date]
            if date.strftime('%A') == 'Friday' and name in partials:
                #find the person's weekday:
                weekday_duty = None
                for i in range(1,6):
                    test_date = date - datetime.timedelta(days = i)
                    if test_date in dates and self.on_duty[test_date] == name:
                        weekday_duty = test_date
                        break
                #assign someone from the replacement list to that duty if it exists
                if weekday_duty != None:
                    replacement_name = replacement_list[0]
                    #make sure this person doesn't have the following Saturday duty
                    saturday = date + datetime.timedelta(days = 1)
                    if saturday in dates and replacement_name == self.on_duty[saturday]:
                        #if they do, go to the next person
                        replacement_name = replacement_list[1]
                    try:
                        set_on_duty(weekday_duty, replacement_name)
                    except:
                        #if that person is also not available, go to the next person.
                        index += 1
                        if index >= len(replacement_list):
                            index = 0
                        replacement_name = replacement_list[index]
                        self.set_on_duty(weekday_duty,replacement_name)
                    #and move the person who actually got this extra duty assigned to the end of the list
                    replacement_list.remove(replacement_name)
                    replacement_list.append(replacement_name)


    def rebalance_weekdays(self):
        weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        def calculate_overload():
            share = self.calculate_shares()
            overload = {}
            for fac in self.faculty:
                overload[fac.name] = len(fac.get_duty_dates('dorm')) - share[fac.load]
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

    def assign_weekday_presets(self, i, weekday_presets):
        self.weekday_presets[i] = weekday_presets

    def assign_weekdays(self):
        #assign default weekdays
        weekday_defaults = {}
        for i in range(3):
            weekday_defaults[i] = self.assign_weekday_defaults(self.weekday_presets[i])

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
        self.set_hospital_runs()

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



