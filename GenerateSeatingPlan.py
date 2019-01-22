#!/usr/bin/env python
# -*- coding: utf-8 -*-
## auto last change for vim and Emacs: (whatever comes last)
## Latest change: Mon Mar 08 11:49:34 CET 2010
## Time-stamp: <2013-11-27 07:52:04 vk>
"""
GenerateSeatingPlan.py
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>
:license: GPL v2 or any later version

See USAGE below for details!

FIXXME:
    * look for the string FIXXME to improve this script
    * Sanity checks all over (cmd line parameters, CSV file, ...)
    * probably: if -p is given, ask for proceeding after displaying ASCII seating plan
    * re-write random assignment of seats so that seats are filled from the front (and only last seats may stay empty)
    * check seed parameter

"""

## for general and jpilot reading:
import logging
import os
from optparse import OptionParser
from random import *

## for CSV
import csv

## debugging:   for setting a breakpoint:  pdb.set_trace()
#import pdb

##        ===========================
##         How to add a lecture room
##        ===========================
##
##    Add a line below with following format:
##
##    NAME_OF_ROOM = { 'rows': NUMBER_OF_ROWS, 'columns': NUMBER_OF_SEATS_PER_ROW, 'name': "HUMAN READABLE NAME", 'seatstoomit': [ LIST OF SEATS THAT CAN NOT BE USED ] }
##
##    ... and ...
##
##    Add an entry to LIST_OF_LECTURE_ROOMS with:
##    { 'name': "SHORT_NAME_OF_ROOM", 'data': NAME_OF_ROOM }   ... with NAME_OF_ROOM is exactly the same name as above
##
## Details:
##
##  * General: avoid german umlauts due to character encoding issues
##        with LaTeX and ASCII output
##  * NUMBER_OF_ROWS: be careful: some lecture rooms have rows
##        that can not be used for exam purposes. For example
##        some rooms do not provide a table for the very first
##        row
##  * "HUMAN READABLE NAME" will be used for printouts
##  * LIST OF SEATS THAT CAN NOT BE USED: some rooms have seats
##        that can not be used because they do not exist or are
##        occupied with something else
##        Comma separated list elements look like: [ 3, 4 ] which
##        means row three and seat four
##  * SHORT_NAME_OF_ROOM: is used for command line argument
##        Must not continue special characters nor spaces!
##  * NAME_OF_ROOM: is used for referring from LIST_OF_LECTURE_ROOMS
##        to the detailed data sets. Please make sure, that they match
##        Must not continue special characters nor spaces!

#NOTE: i7 was refurbished in 2013 and those are the values for the old i7 which have to be updated:
#OLD# HS_i7 = {'rows': 15,
#OLD#         'columns': 16,
#OLD#         'name': "Hoersaal i7",
#OLD#         'seatstoomit': [[1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [1, 8],
#OLD#             [1, 9], [1, 10], [1, 11], [1, 12], [1, 13], [1, 14], [1, 15], [1, 16],
#OLD#             [2, 1], [2, 2], [3, 1], [3, 2],
#OLD#             [4, 1], [4, 2], [5, 1], [5, 2], [6, 1], [6, 2], [7, 1], [7, 2],
#OLD#             [15, 1], [15, 2], [15, 11], [15, 12], [15, 13], [15, 14], [15, 15], [15, 16]
#OLD#             ]}

## Roderick Bloem 20130128, from TUGonline.
HS_i1 = { 'rows': 9,
          'columns':13,
          'name': "Hoersaal i1",
          'seatstoomit': [] }

HS_i11 = {'rows': 10,
        'columns': 9,
        'name': "Hoersaal i11",
        'seatstoomit': [[10, 4], [10, 5], [10, 6]]}

HS_i12 = {'rows': 10,
        'columns': 13,
        'name': "Hoersaal i12",
        'seatstoomit': [[10, 6], [10, 7], [10, 8], [10, 11], [10, 12], [10, 13]]}
        #'seatstoomit': [[10, 6], [10, 7], [10, 8]]}

HS_i13 = {'rows': 14,
        'columns': 22,
        'name': "Hoersaal i13",
        'seatstoomit': [[14, 10], [14, 11], [14, 12], [14, 13],
                        [15,20],[15,21],[15,22], # no chair
        ]}

HS_i14 = {'rows': 9,
        'columns': 4,
        'name': "Hoersaal i14",
        'seatstoomit': []}


## RB 20140119, not checked
HS_A = {
    'rows': 10,
    'columns': 15,
    'name': "Hoersaal A",
    'seatstoomit': [ [9,1], [9,15], [10,1], [10,2], [10,14], [10,15]]
}

HS_B = {'rows': 10,
        'columns': 16,
        'name': "Hoersaal B",
        'seatstoomit': []}

HS_D = {'rows': 6,
        'columns': 10,
        'name': "Hoersaal D",
        'seatstoomit': [[6,9], [6,10] ]}

HS_G = {'rows': 12,
        'columns': 20,
        'name': "Hoersaal G",
        'seatstoomit': []}


## RB 20130527. Checked 20140120.
## First row does not have tables
## added handicap: seats are not numbered.
HS_H = {
  'rows' : 11,
  'columns' : 17,
  'name' : "Hoersaal HS H",
  'seatstoomit': [[1,1],[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8],[1,9],[1,10],[1,11],[1,12],[1,13],[1,14],[1,15],[1,16],[1,17],[1,18],[1,19], [2,18],[2,19], [3,18],[3,19], [4,18],[4,19], [5,18],[5,19], [6,19], [7,19],  [9,1],[9,19], [10,1],[10,2],[10,3],[10,4],[10,16],[10,17],[10,18],[10,19], [11,1],[11,2],[11,3],[11,4],[11,17],[11,18],[11,19] ]
}

## Roderick Bloem 20130128. TUGonline claims 9 columns, but I find that
## unrealistic.  The first two rows are separate tables, but they were
## available when I held an exam there.
HS_VI = { 'rows': 11,
          'columns': 8,
          'name': "Hoersaal VI",
          'seatstoomit' : []
##          'seatstoomit': [ [1, 1], [1,2], [1,3], [1,4], [1,5], [1,6], [1,7], [1,8], [1,9], [2,1], [2,2], [2,3], [2,4], [2,5], [2,6], [2,7], [2,8], [2,9]]
}

HS_P1 = {'rows': 19,
        'columns': 26,
        'name': "Hoersaal P1",
        'seatstoomit': []}

HS_test1 = {'rows': 4,
        'columns': 7,
        'name': "Test-Hoersaal",
        'seatstoomit': [[4, 1], [4, 2], [4, 3], [3, 7]]}

LIST_OF_LECTURE_ROOMS = [\
#OLD#        {'name': "HS_i7", 'data': HS_i7}, \
        {'name': "HS_i11", 'data': HS_i11}, \
        {'name': "HS_i12", 'data': HS_i12}, \
        {'name': "HS_i13", 'data': HS_i13}, \
        {'name': "HS_i14", 'data': HS_i14}, \
        {'name': "HS_A", 'data': HS_A }, \
        {'name': "HS_B", 'data': HS_B}, \
        {'name': "HS_D", 'data': HS_D}, \
        {'name': "HS_G", 'data': HS_G}, \
        {'name': "HS_H", 'data': HS_H }, \
        {'name': "HS_P1", 'data': HS_P1}, \
        {'name': "HS_VI", 'data': HS_VI },\
        {'name': "test1", 'data': HS_test1} \
        ]

BASE_FILE_NAME = "Students"
NAME_OF_TXT_FILE_WITHOUT_EXTENSION = "Students"


## ======================================================================= ##
##                                                                         ##
##         You should NOT need to modify anything below this line!         ##
##                                                                         ##
## ======================================================================= ##

TEMP_FILENAME_PART_DESCRIBING_SEATING_PLAN = "_Seating_Plan_by_Lastname"
TEMP_FILENAME_PART_DESCRIBING_CHECKLIST = "_Checklist_by_Seat"
TEMP_FILENAME_PART_DESCRIBING_TABLE_FORMAT = "_Seating_Plan_Table_Format"

TEMP_FILENAME_STUDENTS_BY_LASTNAME_TEXFILE = "temp_students_by_lastname.tex"
FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION = BASE_FILE_NAME + TEMP_FILENAME_PART_DESCRIBING_SEATING_PLAN

TEMP_FILENAME_STUDENTS_BY_SEATS_TEXFILE = "temp_students_by_seats.tex"
FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION = BASE_FILE_NAME + TEMP_FILENAME_PART_DESCRIBING_CHECKLIST

FILENAME_MAIN_TABLE_WITHOUT_EXTENSION = BASE_FILE_NAME + TEMP_FILENAME_PART_DESCRIBING_TABLE_FORMAT

LECTURE_ROOM_DEFAULT_VALUE = HS_i13
LECTURE_ROOM = LECTURE_ROOM_DEFAULT_VALUE

string_of_all_known_lecture_room_names = ""
for room in LIST_OF_LECTURE_ROOMS:
    string_of_all_known_lecture_room_names += room['name'] + " "

## 1 ... one student, one free seat, one student, ...
## 2 ... two students, one free seat, two students, ...
SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT_DEFAULT_VALUE = 1
SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT = SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT_DEFAULT_VALUE

## 1 ... one row with students, one empty row, one row with students, ...
## 2 ... two rows with students, one empty row, two rows with students, ...
ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER_DEFAULT_VALUE = 1
ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER = ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER_DEFAULT_VALUE

NUM_FREE_SEATS_DEFAULT_VALUE = 1
NUM_FREE_SEATS = NUM_FREE_SEATS_DEFAULT_VALUE

NUM_FREE_ROWS_DEFAULT_VALUE = 1
NUM_FREE_ROWS = NUM_FREE_ROWS_DEFAULT_VALUE

SEED = float(0.0)  # default

USAGE = "\n\
         %prog --lr KNOWN_ROOM STUDENTS.csv\n\
\n\
GenerateSeatingPlan.py takes a CAMPUSonline CSV file including the students\n\
attending an exam and generates a randomized seating plan for a specific\n\
lecture room.\n\
\n\
Several things can be manipulated according to your needs. \n\
\n\
  :URL:        https://github.com/novoid/GenerateSeatingplan.py\n\
  :copyright:  (c) 2010-2012 by Karl Voit <Karl.Voit@IST.TUGraz.at>\n\
  :license:    GPL v2 or any later version\n\
  :bugreports: <Karl.Voit@IST.TUGraz.at>\n\
\n\
Run %prog --help for usage hints\n"

parser = OptionParser(usage=USAGE)

parser.add_option("-c", "--csvfile", dest="students_csv_file",
                  help="CSV file of students in CAMPUSonline format. You can add columns but original header line is required.", metavar="FILE")

parser.add_option("--lr", "--lecture-room", dest="lecture_room",
                help="the short name of a known lecture room. so far, following lecture rooms are supported: " + \
                      str(string_of_all_known_lecture_room_names), metavar="NAME")

parser.add_option("--sa", "--students_adjoined", dest="students_side_by_side",
                  help="that many students are sitting right beneath each other before the next empty seat(s)", metavar="INT")

parser.add_option("--ra", "--filled_rows_adjoined", dest="occupied_row_before_empty_line",
                  help="that many rows are being filled with students before the next empty row(s)", metavar="INT")

parser.add_option("--fs", "--free_seats_to_seperate", dest="num_free_seats",
                  help="that many seats are empty before the next student sits", metavar="INT")

parser.add_option("--fr", "--free_rows_to_seperate", dest="num_free_rows",
                  help="that many rows are empty before the next row is filled", metavar="INT")

parser.add_option("-s", "--seed", dest="seed", type="float",
                  help="sets random seed for shuffling students (default 0.0)", metavar="FLOAT")

parser.add_option("-p", "--pdf", dest="pdf", action="store_true",
                  help="generates a PDF file with alphabetical student names and seating (requires pdflatex with savetrees, longtable, hyperref, and KOMA)")

parser.add_option("-t", "--table", dest="table", action="store_true",
                  help="generates a seating plan in (HTML) table format.")

parser.add_option("-u", "--tableturn", dest="tableturn", action="store_true",
                  help="Writes the table upside down (view for lecturer). Might not work with all browsers.")

parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")

parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="do not output anything but just errors on console")

parser.add_option("--checklist", dest="checklist", action="store_true",
                  help="creates a list of students orderd by seat")

parser.add_option("--suffix", dest="filenamesuffix",
                  help="added suffix for filename (e.g. '_termin_20170102", metavar="STR")

parser.add_option("--title", dest="title",
                  help="add identifier for Lecture Name or time slot...", metavar="STR")

(options, args) = parser.parse_args()

if options.filenamesuffix:
    FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION = FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + str(options.filenamesuffix)
    FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION = FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + str(options.filenamesuffix)
    FILENAME_MAIN_TABLE_WITHOUT_EXTENSION = FILENAME_MAIN_TABLE_WITHOUT_EXTENSION + str(options.filenamesuffix)

if options.title:
    SEATING_PLAN_TITLE = options.title

class vk_FileNotFoundException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.CRITICAL, format=FORMAT)
    else:
        FORMAT = "%(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)


def ReadInStudentsFromCsv(csvfilename):
    # FIXXX
    csvReader = csv.DictReader(open(csvfilename), delimiter=';', quotechar='"')
    students_list = []

    for row in csvReader:
        students_list.append(row)

    return students_list


def PrintOutSeats(lecture_room, list_of_seats):
    """Plot an ASCII graph of the lecture room with all potential used seats (to show seating scheme)"""

    linestring = ""
    if len(list_of_seats) < 1:
        logging.warning("list_of_seats is empty, so no seat is occupied. looks like internal error.")
    ## logging.debug("number of seats in list_of_seats: %s" % str(len(list_of_seats)) )

    print "\nLegend:   #  ... potential seat      -  ... empty seat"
    print   "          S  ... student sitting     X  ... seat not available"
    print   "      row 1  ... first row near blackboard"

    print "\n------    Seating Scheme for Lecture Room \"" + lecture_room['name'] + "\"   ------\n"
    print   "              --Front--"

    for currentrow in range(1, lecture_room['rows'] + 1):

        linestring = "   row " + str(currentrow).rjust(2) + ":  "

        for currentseat in range(1, lecture_room['columns'] + 1):
            if [currentrow, currentseat] in lecture_room['seatstoomit']:
                linestring += "X "
            elif [currentrow, currentseat] in list_of_seats:
                linestring += "# "
            else:
                linestring += "- "

        print linestring
        linestring = ''


def PrintOutSeatsWithStudents(lecture_room, list_of_students):
    """Plot an ASCII graph of the lecture room with all seated students marked"""

    linestring = ""
    if len(list_of_students) < 1:
        logging.warning("list_of_seats is empty, so no seat is occupied. looks like internal error.")

    print "\n------    Seating Plan with students for Lecture Room \"" + lecture_room['name'] + "\"   ------\n"
    print   "              --Front--"

    for currentrow in range(1, lecture_room['rows'] + 1):

        linestring = "   row " + str(currentrow).rjust(2) + ":  "

        for currentseat in range(1, lecture_room['columns'] + 1):

            seat_is_defined = False

            if [currentrow, currentseat] in lecture_room['seatstoomit']:
                linestring += "X "
                seat_is_defined = True
                continue

            ## pretty dumb "brute force" search for a student, sitting on current seat
            for student in list_of_students:
                if student['seat'] == [currentrow, currentseat]:
                    linestring += "S "
                    seat_is_defined = True

            if not seat_is_defined:
                linestring += "- "

        print linestring
        linestring = ''
    print  # one final line to seperate


def FillRowWithStudentsOrLeaveEmpty(lecture_room, currentrow, list_of_occupied_seats):

    ## initialize things before filling a row with students:
    current_num_of_students_close_together = 0
    current_num_of_empty_seats = 0
    filling_seats = True

    ## iterate over the seats in a row:
    for currentseat in range(1, lecture_room['columns'] + 1):

        #logging.debug("---row %s seat %s stud_close %s" % ( str(currentrow), str(currentseat), str(current_num_of_students_close_together) )   )

        ## filling_seats means that there are not too many students right beneath each other:
        if filling_seats:

            #logging.debug("o  row %s seat %s occupied" % (str(currentrow), str(currentseat)))
            list_of_occupied_seats.append([currentrow, currentseat])
            current_num_of_students_close_together += 1

            ## if enough students are seated beneath each other, continue next time with empty seats:
            if current_num_of_students_close_together >= SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT:
                current_num_of_students_close_together = 0
                if NUM_FREE_SEATS > 0:
                    filling_seats = False
                    current_num_of_empty_seats = 0

        else:  # not filling seats, generate empty seats between students

            current_num_of_empty_seats += 1

            ## continue with seating students again
            if current_num_of_empty_seats >= NUM_FREE_SEATS:
                current_num_of_empty_seats = 0
                current_num_of_students_close_together = 0
                filling_seats = True
                continue  # with next seat

            ## not enough free seats, continue with empty seats
            elif current_num_of_empty_seats < NUM_FREE_SEATS:
                continue  # with next seat

    return list_of_occupied_seats


def GenerateListOfAllSeats(lecture_room):
    """Generates a (dumb) list of all seats *not* considering seats to omit"""

    logging.debug("seats per row:  %s" % str(lecture_room['columns']))
    logging.debug("number of rows: %s" % str(lecture_room['rows']))
    logging.debug("number of students sitting right beneath each other:  %s" % str(SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT))
    logging.debug("number of rows filled with students before empty row: %s" % str(ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER))

    current_num_of_filled_rows = 0
    current_num_of_empty_rows = 0
    filling_row = True
    list_of_occupied_seats = []

    ## iterate over the rows:
    for currentrow in range(1, lecture_room['rows'] + 1):

        #logging.debug("r  starting now in row %s" % str(currentrow) )

        ## filling_row == True if currentrow should be filled with students
        if filling_row:

            current_num_of_filled_rows += 1

            ## fill me the row:
            list_of_occupied_seats = FillRowWithStudentsOrLeaveEmpty(lecture_room, currentrow, list_of_occupied_seats)

            if current_num_of_filled_rows >= ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER:
                ## next row should be an empty one

                current_num_of_filled_rows = 0
                if NUM_FREE_ROWS > 0:
                    filling_row = False
                #logging.debug("skipping row %s" % str(currentrow) )
                continue  # in next row

        ## not filling rows: keep row empty
        else:

            current_num_of_empty_rows += 1

            ## next row should be filled with students again
            if current_num_of_empty_rows >= NUM_FREE_ROWS:
                current_num_of_empty_rows = 0
                filling_row = True
                continue  # in next row

            ## keep on with empty rows
            elif current_num_of_empty_rows < NUM_FREE_ROWS:
                continue  # in next row

    logging.debug("number of (dumb) seats not considered seats to omit: %s" % str(len(list_of_occupied_seats)))
    ## print str(list_of_occupied_seats)

    return list_of_occupied_seats


def SelectRandomListElementAndRemoveItFromList(list):

    if list != []:
        list_element_index = randrange(len(list))
        list_element = list[list_element_index]
        list[list_element_index] = list[-1]
        del list[-1]
        return list_element
    else:
        return None


def GenerateRandomizedSeatingPlan(list_of_students, list_of_available_seats):
    shuffle(list_of_students)

    ## randomize students over all seats:
    for student in list_of_students:
        student['seat'] = SelectRandomListElementAndRemoveItFromList(list_of_available_seats)

    return list_of_students


def GenerateTextfileSortedByStudentLastname(lecture_room, list_of_students_with_seats):
    # well we need to sort the student list if the function name says so!
    list_of_students_with_seats.sort(key=lambda s: s['FAMILY_NAME_OF_STUDENT'])

    file = open(FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.txt', 'w')

    file.write("               Seating plan     " + lecture_room['name'] + "      by last name\n\n")

    filler = " "
    for student in list_of_students_with_seats: # FIXXXXXME Bug utf8 chars are counted as 2 chars and dots are omitted
        file.write("{lastname:25}{filler}{firstname:23}{filler}{mnr:^10} row {row:>5} seat {seat:>3}".format(
            filler=filler,
            lastname=student['FAMILY_NAME_OF_STUDENT'].ljust(25,filler),
            firstname=student['FIRST_NAME_OF_STUDENT'].ljust(23,filler),
            mnr=(student['REGISTRATION_NUMBER'][:4] + 'XXX').ljust(10,filler),
            row="{row}/{rowchar}".format(row=str(student['seat'][0]),rowchar=str(chr(64 + student['seat'][0]))),
            seat=str(student['seat'][1]).rjust(3) + "\n" + "-"*80 + "\n"
            )
            )

def GenerateLatexfileSortedByStudentLastname(lecture_room, list_of_students_with_seats):
    # well we need to sort the student list if the function name says so!
    list_of_students_with_seats.sort(key=lambda s: s['FAMILY_NAME_OF_STUDENT'])

    file = open(TEMP_FILENAME_STUDENTS_BY_LASTNAME_TEXFILE, 'w')

    for student in list_of_students_with_seats:
        file.write("\\vkExamStudent{" + student['FAMILY_NAME_OF_STUDENT'] + '}{' + \
            student['FIRST_NAME_OF_STUDENT'] + '}{' + \
            student['REGISTRATION_NUMBER'][:4] + 'XXX}{' + \
            str(student['seat'][0]) + '}{' + \
            str(chr(64 + student['seat'][0])) + '}{' + \
            str(student['seat'][1]) + '}' + "\n")
    file.flush()
    os.fsync(file.fileno())


def GenerateHtmlFileWithTableFormat(lecture_room, list_of_students_with_seats):

    # FIXXME: Sizing needs some improvement.
    # FIXXME: Turning text upside down might not work for all browsers.

    htmlfile = open(FILENAME_MAIN_TABLE_WITHOUT_EXTENSION + '.html', 'w')

    htmlfile.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n')
    htmlfile.write('        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
    htmlfile.write('<html xmlns="http://www.w3.org/1999/xhtml">\n')
    htmlfile.write('<head>\n')
    htmlfile.write(' 	<title>Seating Plan</title>\n')
    htmlfile.write('	<meta http-equiv="content-type"\n')
    htmlfile.write('		content="text/html;charset=UTF-8" />\n')
    htmlfile.write('		<STYLE type="text/css">\n')
    htmlfile.write('		table {table-layout: fixed;}\n')
    htmlfile.write('    td {border: 1px solid #000000; text-align: center; width: 100px; font-size: 10pt; height: 60px; %s}\n' \
       % ("webkit-transform: rotate(-180deg); -moz-transform: rotate(-180deg); filter: progid:DXImageTransform.Microsoft.BasicImage(rotation=2);" \
         if options.tableturn else ""))
    htmlfile.write('    .empty {background-color: #EEEEEE}\n')
    htmlfile.write('    .omit {font-style: bold; font-size: 20pt; background-color: #AAAAAA}\n')
    htmlfile.write('    .header {font-size: 20pt; font-style: bold}\n')
    htmlfile.write('    .number {border: 0px}\n')
    htmlfile.write('    </STYLE>\n')
    htmlfile.write('</head>\n')
    htmlfile.write('<body>\n')
    htmlfile.write('<table style="width: %dpx;">\n' % ((lecture_room['columns'] + 1) * 100))
    htmlfile.write('<tr><td class="number">&nbsp;</td><td class="header" colspan="%d" style="width: %dpx">Front</td></tr>\n' % \
       (lecture_room['columns'], (lecture_room['columns']) * 100))
    htmlfile.write('<tr>\n')
    htmlfile.write('<td class="number">&nbsp;</td>')
    for i in range(1, lecture_room['columns'] + 1):
        htmlfile.write('<td class="number">%d</td>' % i)
    htmlfile.write('</tr>\n')
    for i in range(1, lecture_room['rows'] + 1):
        htmlfile.write('<tr>\n')
        htmlfile.write('<td class="number">%d</td>' % i)
        for j in range(1, lecture_room['columns'] + 1):
            seat_data = '&nbsp;'
            seat_class = 'empty'
            if [i, j] in lecture_room['seatstoomit']:
                seat_data = 'X'
                seat_class = 'omit'
            students_on_this_seat = [student for student in list_of_students_with_seats if student['seat'] == [i, j]]
            if len(students_on_this_seat) > 1:
                logging.critical("ERROR: More than one student on seat [%d,%d]. This must be an internal error." % (i, j))
            elif len(students_on_this_seat) == 1:
                student = students_on_this_seat[0]
                seat_class = 'occupied'
                seat_data = student['FAMILY_NAME_OF_STUDENT'] + \
                    '<br />' + student['FIRST_NAME_OF_STUDENT'] + \
                    '<br />' + student['REGISTRATION_NUMBER'][:4] + 'XXX'
            htmlfile.write('<td class="%s">%s</td>' % (seat_class, seat_data))
        htmlfile.write('\n</tr>\n')
    htmlfile.write('</table>')

    htmlfile.write('</body>\n')
    htmlfile.write('</html>\n')
    htmlfile.flush()
    os.fsync(htmlfile.fileno())


def compare_students_by_row_and_seat(a, b):

        return cmp(a['seat'][0], b['seat'][0]) or cmp(a['seat'][1], b['seat'][1])


def GenerateTextfileSortedBySeat(lecture_room, list_of_students_with_seats):

    txtfile = open(FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.txt', 'w')
    if options.pdf:
        latexfile = open(TEMP_FILENAME_STUDENTS_BY_SEATS_TEXFILE, 'w')

    ## ASCII/txt file header
    txtfile.write("               Seating plan     " + lecture_room['name'] + "      by seat\n\n")

    for student in sorted(list_of_students_with_seats, compare_students_by_row_and_seat):

        ## write student to ASCII/txt file
        txtfile.write("[ ] " + student['FAMILY_NAME_OF_STUDENT'].ljust(25, '.') + \
            student['FIRST_NAME_OF_STUDENT'].ljust(20, '.') + \
            student['REGISTRATION_NUMBER'] + \
            "  row " + str(student['seat'][0]).rjust(3) + "/" + str(chr(64 + student['seat'][0])) + \
            "  seat " + str(student['seat'][1]).rjust(3) + "\n\n")

        if options.pdf:

            probablyshortenedfirstname = ""
            threshold_full_name = 25  # try to shorten first names when full name exceeds this threshold and ...
            threshold_first_name = 8  # ... when first name exceeds this threshold

            ## shorten first name if appropriate:
            if len(student['FIRST_NAME_OF_STUDENT']) + len(student['FAMILY_NAME_OF_STUDENT']) > threshold_full_name and \
                    len(student['FIRST_NAME_OF_STUDENT']) > threshold_first_name:
                        probablyshortenedfirstname = student['FIRST_NAME_OF_STUDENT'][:threshold_first_name - 3] + '\ldots{}'
                        logging.debug("shortened first name of \"" + student['FIRST_NAME_OF_STUDENT'] + " " + \
                                student['FAMILY_NAME_OF_STUDENT'] + "\" to \"" + probablyshortenedfirstname + \
                                "\" because it exceeds threshold for long names")
            else:
                probablyshortenedfirstname = student['FIRST_NAME_OF_STUDENT']

            ## write student to LaTeX temporary file:
            latexfile.write("\\vkExamStudent{" + student['FAMILY_NAME_OF_STUDENT'] + '}{' + \
                probablyshortenedfirstname + '}{' + \
                student['REGISTRATION_NUMBER'] + '}{' + \
                str(student['seat'][0]) + '}{' + \
                str(chr(64 + student['seat'][0])) + '}{' + \
                str(student['seat'][1]) + '}' + "\n")

    if options.pdf:
        latexfile.flush()
        os.fsync(latexfile.fileno())


def GenerateLatexMainFileSortedByLastname(lecture_room):

    content = '''\\documentclass[%
14pt,%
%a4paper,%
oneside,%
headinclude,%
footexclude,%
openright%
]{scrartcl}

%% encoding:
%\\usepackage[ansinew]{inputenc}
%\\usepackage{ucs}
\\usepackage[utf8x]{inputenc}  %% Sorry, problems with Umlauts in CSV forced me to stay at ansinew
%\\usepackage[utf8]{inputenc}
%\\usepackage[T1]{fontenc}
\\usepackage[ngerman]{babel} % Sprache
%% use up as much space as possible:
\\usepackage{savetrees}

%% using a loooong table possible over several pages:
\\usepackage{longtable}

\\pdfcompresslevel=9

\\usepackage[%
  pdftitle={Seating Plan}, %
  pdfauthor={}, %
  pdfsubject={Exam}, %
  pdfcreator={Accomplished with LaTeX2e and pdfLaTeX with hyperref-package under Debian GNU/Linux. No anmimals, MS-EULA or BSA-rules were harmed.},
  pdfproducer={GenerateSeatingPlan.py by Karl Voit},
  pdfkeywords={Seating Plan, Exam},
  a4paper=true, %
  pdftex=true, %
  bookmarks=false, %
  bookmarksopen=false, % when starting with AcrobatReader, the Bookmarkcolumn is opened
  pdfpagemode=None,% None, UseOutlines, UseThumbs, FullScreen
  plainpages=false, % correct, if pdflatex complains: ``destination with same identifier already exists''
  colorlinks=false % turn off colored links (better for printout versions)
]{hyperref}

%% header and footer:
\\usepackage{scrpage2}
\\pagestyle{scrheadings}
\\clearscrheadings
\\clearscrplain
\\ifoot{\\scriptsize{}page~\\pagemark}
%\\ofoot{\\tiny{}Generated using GenerateSeatingPlan.py by Karl Voit}

\\begin{document}

\\newcommand{\\vkExamStudent}[6]{%%
    #1 & #2 & #3 & #4 & #6  \\\\[0.5em]
}%%

\\sffamily
\\newcommand{\\vkHeaderSettings}[1]{\\textbf{\\large{#1}}}

\\begin{longtable}{lllrr}
\\multicolumn{5}{c}{\\scshape\\Large ''' + SEATING_PLAN_TITLE + '''} \\\\[5pt]
\\multicolumn{5}{c}{\\scshape\\Large Seating Plan ''' + lecture_room['name'] + '''} \\\\[5pt]
\\multicolumn{2}{c}{\\vkHeaderSettings{Name}} & {\\vkHeaderSettings{Matr.Nr.}} & \\multicolumn{1}{c}{\\vkHeaderSettings{Row}} & {\\vkHeaderSettings{Seat}}  \\\\[5pt]
\\hline
\\hline \\\\[-5pt]
\\endhead
\\input{''' + TEMP_FILENAME_STUDENTS_BY_LASTNAME_TEXFILE + '''}
\\hline
\\end{longtable}

\\end{document}
%% end
'''

    file = open(FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.tex', 'w')

    file.write(content.encode('utf8'))
    file.flush()
    os.fsync(file.fileno())


def GenerateLatexMainFileSortedBySeat(lecture_room):

    content = '''\\documentclass[%
12pt,%
a4paper,%
twoside,%
headinclude,%
footexclude,%
twocolumn,%
parskip=half-,%
openright%
]{scrartcl}

%% encoding:
%\\usepackage[ansinew]{inputenc}
%\\usepackage{ucs}
\\usepackage[utf8x]{inputenc}  %% Sorry, problems with Umlauts in CSV forced me to stay at ansinew

%% use up as much space as possible:
\\usepackage{savetrees}

%% using a loooong table possible over several pages:
\\usepackage{longtable}

\\pdfcompresslevel=9

\\usepackage[%
  pdftitle={Exam Checklist for Lecture Room ''' + lecture_room['name'] + '''}, %
  pdfauthor={}, %
  pdfsubject={Exam, ''' + lecture_room['name'] + '''}, %
  pdfcreator={Accomplished with LaTeX2e and pdfLaTeX with hyperref-package under Debian GNU/Linux. No anmimals, MS-EULA or BSA-rules were harmed.},
  pdfproducer={Checklist of GenerateSeatingPlan.py by Karl Voit},
  pdfkeywords={Checklist, Seating Plan, Exam},
  a4paper=true, %
  pdftex=true, %
  bookmarks=false, %
  bookmarksopen=false, % when starting with AcrobatReader, the Bookmarkcolumn is opened
  pdfpagemode=None,% None, UseOutlines, UseThumbs, FullScreen
  plainpages=false, % correct, if pdflatex complains: ``destination with same identifier already exists''
  colorlinks=false % turn off colored links (better for printout versions)
]{hyperref}

%% header and footer:
\\usepackage{scrpage2}
\\pagestyle{scrheadings}
\\clearscrheadings
\\clearscrplain
\\chead{Exam Checklist of Lecture Room ''' + lecture_room['name'] + '''}
\\ifoot{\\scriptsize{}page~\\pagemark}
%\\ofoot{\\tiny{}Generated using GenerateSeatingPlan.py by Karl Voit}

\\begin{document}

\\newcommand{\\vkExamStudent}[6]{%%
\\makebox[\\linewidth][l]{$\\bigcirc$~#2~{\\textbf{{#1}}};~#3,~R#4~S#6}\\\\[3mm]%%
}%%

\\sffamily
\\newcommand{\\vkHeaderSettings}[1]{\\textbf{#1} }

\\input{''' + TEMP_FILENAME_STUDENTS_BY_SEATS_TEXFILE + '''}

\\end{document}
%% end'''

    file = open(FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.tex', 'w')

    file.write(content)
    file.flush()
    os.fsync(file.fileno())


def InvokeLaTeX():

    ## FIXXME: implement a test, if pdflatex is found in path like:
    ## if not py.path.local.sysfind("pdflatex"):
    ##     logging.critical("ERROR: pdflatex could not be found on your system!")
    ##     os.sys.exit(7)

    if (os.system('pdflatex ' + FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.tex') or
        os.system('pdflatex ' + FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.tex')):
        logging.critical("ERROR: pdflatex for list by lastname returned with an error.")
        logging.critical("You can try manually by invoking \"pdflatex " + FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + ".tex\"")
        os.sys.exit(8)

    if options.checklist:
        if (os.system('pdflatex ' + FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.tex') or \
            os.system('pdflatex ' + FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.tex')):
            logging.critical("ERROR: pdflatex for list by seats returned with an error.")
            logging.critical("You can try manually by invoking \"pdflatex " + FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + ".tex\"")
            os.sys.exit(9)


def DeleteTempLaTeXFiles():

    ## FIXXME: check at tool start, if files with these names
    ##   are already in current directory and issue a warning
    ##   that these files will be deleted!

    if options.verbose:
        print "omitting deletion of temporary files (because of verbose mode)"
    else:
        logging.info("deleting temporary LaTeX files ...")
        os.remove(FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.tex')
        os.remove(FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.log')
        os.remove(FILENAME_MAIN_BY_LASTNAME_WITHOUT_EXTENSION + '.aux')
        os.remove(TEMP_FILENAME_STUDENTS_BY_LASTNAME_TEXFILE)
        if options.checklist:
            os.remove(TEMP_FILENAME_STUDENTS_BY_SEATS_TEXFILE)
            os.remove(FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.tex')
            os.remove(FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.log')
            os.remove(FILENAME_MAIN_BY_SEATS_WITHOUT_EXTENSION + '.aux')
        logging.info("deleting temporary LaTeX files finished")


def main():
    """Main function [make pylint happy :)]"""

    print "   GenerateSeatingPlan.py - generating random seating plans for exams\n"
    print "          (c) 2010 by Karl Voit <Karl.Voit@IST.TUGraz.at>"
    print "              GPL v2 or any later version\n"

    handle_logging()

    if not options.students_csv_file:
        logging.critical("ERROR: No students CSV file given")
        os.sys.exit(1)

    if not os.path.isfile(options.students_csv_file):
        logging.critical("ERROR: Students CSV file could not be found")
        os.sys.exit(2)

    ## FIXXME: implement additional command line parameter checks

    global ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER
    if options.occupied_row_before_empty_line:
        logging.debug("default value of ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER: %s" % ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER)
        ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER = int(options.occupied_row_before_empty_line)
        logging.debug("ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER " +
            "is overwritten by command line parameter: %s" % ROWS_WITH_STUDENTS_TO_KEEP_TOGETHER)

    global SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT
    if options.students_side_by_side:
        logging.debug("default value of SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT: %s" % SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT)
        SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT = int(options.students_side_by_side)
        logging.debug("SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT " +
            "is overwritten by command line parameter: %s" % SEATS_WITH_STUDENTS_BEFORE_FREE_SEAT)

    global NUM_FREE_SEATS
    if options.num_free_seats:
        logging.debug("default value of NUM_FREE_SEATS: %s" % NUM_FREE_SEATS)
        NUM_FREE_SEATS = int(options.num_free_seats)
        logging.debug("NUM_FREE_SEATS " +
            "is overwritten by command line parameter: %s" % NUM_FREE_SEATS)

    global NUM_FREE_ROWS
    if options.num_free_rows:
        logging.debug("default value of NUM_FREE_ROWS: %s" % NUM_FREE_ROWS)
        NUM_FREE_ROWS = int(options.num_free_rows)
        logging.debug("NUM_FREE_ROWS " +
            "is overwritten by command line parameter: %s" % NUM_FREE_ROWS)

    global LECTURE_ROOM
    if options.lecture_room:
        logging.debug("default value of LECTURE_ROOM: %s" % LECTURE_ROOM['name'])
        LECTURE_ROOM = ""
        for room in LIST_OF_LECTURE_ROOMS:
            ## search for matching known lecture room
            if room['name'] == options.lecture_room:
                LECTURE_ROOM = room['data']
        if LECTURE_ROOM == "":
            logging.critical("ERROR: Sorry, lecture room \"%s\" is not recognised yet." % options.lecture_room)
            logging.critical("Known rooms are: %s" % string_of_all_known_lecture_room_names)
            os.sys.exit(4)

        logging.debug("LECTURE_ROOM is overwritten by command line parameter: %s" % LECTURE_ROOM['name'])

    global SEED
    if options.seed:
        logging.debug("default value of SEED: %s" % SEED)
        SEED = options.seed
        logging.debug("SEED " +
            "is overwritten by command line parameter: %s" % SEED)

    # Initializing the PRNG with a seed value.
    # This is done once at this point. This should suffice
    # to produce deterministic re-runs.
    seed(SEED)

    logging.debug("Student CSV file found")

    list_of_students = ReadInStudentsFromCsv(options.students_csv_file)
    print list_of_students[0]
    #logging.info("Number of students:  %s" % str(len(list_of_students)))
    print "Number of students:  %s" % str(len(list_of_students))

    ## generate list of all seats and remove seats to omit from lecture room:
    list_of_available_seats = [x for x in GenerateListOfAllSeats(LECTURE_ROOM) if x not in LECTURE_ROOM['seatstoomit']]

    # logging.info("Number of seats:     %s   (using current seating scheme)" % str(len(list_of_available_seats)) )
    print "Number of seats:     %s   (using current seating scheme)" % str(len(list_of_available_seats))

    ## just the potential seating plan (without students)
    PrintOutSeats(LECTURE_ROOM, list_of_available_seats)

    missing_seats = len(list_of_students) - len(list_of_available_seats)
    if missing_seats > 0:
        logging.critical("\nERROR: With current seating scheme, there are %s seats missing!\n" % str(missing_seats))
        logging.critical("Tip: try higher values for \"--students_adjoined\", \"--filled_rows_adjoined\",")
        logging.critical("     or lower values for \"--free_seats_to_seperate\", \"--free_rows_to_seperate\".")
        os.sys.exit(3)

    unused_seats_info = "(Unused seats: %s)" % str(len(list_of_available_seats) - len(list_of_students))

    list_of_students_with_seats = GenerateRandomizedSeatingPlan(list_of_students, list_of_available_seats)

    ## the seating plan (showing the students)
    PrintOutSeatsWithStudents(LECTURE_ROOM, list_of_students_with_seats)

    print unused_seats_info

    GenerateTextfileSortedByStudentLastname(LECTURE_ROOM, list_of_students_with_seats)

    if options.checklist:
        GenerateTextfileSortedBySeat(LECTURE_ROOM, list_of_students_with_seats)

    if options.pdf:
        GenerateLatexfileSortedByStudentLastname(LECTURE_ROOM, list_of_students_with_seats)
        GenerateLatexMainFileSortedByLastname(LECTURE_ROOM)
        if options.checklist:
            GenerateLatexMainFileSortedBySeat(LECTURE_ROOM)
        InvokeLaTeX()
        DeleteTempLaTeXFiles()

    if options.table:
        GenerateHtmlFileWithTableFormat(LECTURE_ROOM, list_of_students_with_seats)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################
# vim:foldmethod=indent expandtab ai ft=python tw=120 fileencoding=utf-8 shiftwidth=4
