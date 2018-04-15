#! /usr/bin/python2.5

from __future__ import with_statement #This isn't required in Python 2.6
import os, sys, re
from stat import *

#--------------------------------------- class Slides
class Slides:
    '''represents a set of powerpoint slides'''
    
    def __init__(self):
	'''Constructor'''
	self.title = ''
	self.slide_list = dict()
	self.slide_orders = dict()
	self.current_label = ''
	self.title_regex = re.compile('{ti?t?l?e?: *([^}]*)}')
	self.slide_def_regex = re.compile('#slide:(.*)$')
	self.slide_end_regex = re.compile('#slide_end')
        self.slide_set_regex = re.compile('#ppt:([^,]+), *(.*)$')
	self.match_chords = re.compile('\[[^\]]*\]')
	self.match_commands = re.compile('{[^}]*}')
	self.match_comments = re.compile('^#.*$')
	self.match_spaces = re.compile(' +')
	self.visitLine = lambda line:self.processLine(line)
	self.NO_SLIDE, self.SLIDE = range(2)
	self.state = self.NO_SLIDE
	self.new_line = '\r\n'

    def processLine(self, line):
        #check if the line is a title
        m = self.title_regex.match(line)
        if (m != None):
	    self.title = m.group(1)
        #check if the line is a slide start
    	m = self.slide_def_regex.match(line)
	    if (m != None):
	        self.state = self.SLIDE
     	    self.label = str.strip(m.group(1))
    	    self.slide_list[self.label] = list()
        #check if the line is a slide end
	    m = self.slide_end_regex.match(line)
	    if (m != None):
	        self.state = self.NO_SLIDE
	        self.label = ''
        #check if the line is a slide set
	    m = self.slide_set_regex.match(line)
	    if (m != None):
	        #TODO:pull out set info
	        self.state = self.NO_SLIDE
	        self.label = ''
	        self.slide_orders[m.group(1)] = map(lambda name:str.strip(name), m.group(2).split(','))
	    #process the line
	    if (self.state == self.SLIDE):
	        #filter our the chords
	        line = self.match_chords.sub('', line)
	        #filter our the commands
	        line = self.match_commands.sub('', line)
	        #filter our the comments
	        line = self.match_comments.sub('', line)
	        #remove internal spaces
	        line = self.match_spaces.sub(' ', line)
	        #remove leading/trailing spaces
	        line = str.strip(line)
	        if (line != ''):
		        self.slide_list[self.label].append(line)

    def getSlideSetText(self):
	    '''Return a dictionary of strings representing slide sets'''
	    title = self.title or '-'
	    deck_texts = dict()
	    make_slide = lambda arr: title + self.new_line + reduce(lambda accum, line: accum + self.new_line + line, map(lambda line: '\t' + line, arr))
	    make_deck = lambda deck_def: reduce(lambda x, y: x + y, map(lambda slide_name: make_slide(self.slide_list[slide_name]) + self.new_line, deck_def))
	    for (deck_name, slide_names) in self.slide_orders.iteritems():
	        yield (deck_name, make_deck(slide_names))

#--------------------------------------- class Song
class Song:
    '''represents a song starting with .cho file'''

    def __init__(self,cho_filename):
        '''Constructor'''
        self.cho_filename = cho_filename
        (path,filename) = os.path.split(self.cho_filename)
        self.path = path
        self.name = re.sub('.cho', '', filename)
        self.default_chord_args = '-G -t 12 -c 12 -C Helvetica-Bold -a'

    def getPsPath(self, label, extension):
        filename = 'tmp.' + extension
        return os.path.join('./', filename)

    def getPath(self, label, extension):
        label_to_use = label if (label == '') else '_' + label
        filename = self.name + label_to_use + '.' + extension
        return os.path.join(self.path, filename)

    def getDestinationPath(self, label, extension):
        label_to_use = label if (label == '') else '_' + label
        filename = self.name + label_to_use + '.' + extension
        return os.path.join('D:/Dropbox/Public/Chords/', filename)

    def toPDF(self, chord2ps, ps2pdf, chord2ps_options, label):
        ps_path = self.getPsPath(label, 'ps')
        pdf_path = self.getDestinationPath(label, 'pdf')
        if (isNewer(self.cho_filename, pdf_path)):
            #run chord2ps to produce song_label.ps
            psCommand = chord2ps + ' ' + chord2ps_options + ' -o "' + ps_path + '" "' + self.cho_filename + '"'
            print psCommand
            os.system(psCommand)
            #run ps2pdf to produce song_label.pdf
            pdfCommand = ps2pdf + ' "' + ps_path + '" "' + pdf_path + '"'
            print pdfCommand
            os.system(pdfCommand)

    def toPPT(self, label, slides):
        ppt_path = self.getDestinationPath(label, 'ppt')
        if (isNewer(self.cho_filename, ppt_path)):
            with open(ppt_path, 'w+') as file:
                file.write(slides)

    def getDefaultConversionOptions(self):
        conversion_options = {}
        conversion_options['chord'] = self.default_chord_args
        conversion_options['lyrics'] = '-l -t 12 -a'
        return conversion_options

    def parseToList(self, regex, line):
        m = regex.match(line)
        if (m != None):
            args = m.group(2).rstrip()
            #substitute '%' for default options
            args = re.sub('%', self.default_chord_args, args)
            #return the options
            return (m.group(1), args)

    def getCustomConversionOptions(self):
        conversion_options = {}
        p = re.compile('#convert:([^,]+),(.*)$')
        #open the file, get the option pairs, stick them into a dictionary
        with open(self.cho_filename) as file:
            conversion_options = dict(filter(lambda (pair):pair is not None, map(lambda (line):self.parseToList(p,line), file)))
        #return the options
        return conversion_options
        
    def getConversionOptions(self):
        default_conversion_options = self.getDefaultConversionOptions()
        custom_conversion_options = self.getCustomConversionOptions()
        conversion_options = default_conversion_options
        conversion_options.update(custom_conversion_options)
        return conversion_options

    def getSlideOptions(self):
	    slide_options = Slides()
	    with open(self.cho_filename) as file:
	        map(slide_options.visitLine, file)
	    return slide_options

    def convert(self, chord2ps, ps2pdf):
        map(lambda (key, value): self.toPDF(chord2ps, ps2pdf, value, key), self.getConversionOptions().iteritems())
	    map(lambda (label,text):self.toPPT(label, text), self.getSlideOptions().getSlideSetText())

#--------------------------------------- file utilities

def fileLastModified(filename):
    if (os.path.exists(filename)):
        return os.stat(filename)[ST_MTIME]
    else:
        return 0

def isNewer(fileA, fileB):
    '''The .cho is newer than the .pdf'''
    fileA_mtime = fileLastModified(fileA)
    fileB_mtime = fileLastModified(fileB)
    return (fileA_mtime > fileB_mtime)

def GeneratePathAndMode(top):
    '''return an interator over a list of path/mode tuples'''
    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname)[ST_MODE]
        yield (pathname, mode)

def visit_file_recurse(top, callback):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    switch = lambda (pathname, mode): (S_ISDIR(mode) and visit_file_recurse(pathname, callback)) or (S_ISREG(mode) and callback.visit(pathname))
    map(switch, GeneratePathAndMode(top))

#--------------------------------------- class ChordFileVisitor

class ChordFileVisitor:
    '''a visitor for .cho files'''

    def __init__(self):
        '''Constructor'''

    def visit(self, filename):
        if (re.search('.cho$', filename)):
            song = Song(filename)
            song.convert('chord/chord', 'ps2pdf')

#--------------------------------------- main

if __name__ == '__main__':
    visitor = ChordFileVisitor()
    visit_file_recurse(sys.argv[1], visitor)
