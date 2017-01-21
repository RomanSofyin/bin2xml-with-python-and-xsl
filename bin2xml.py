#!/usr/bin/python

#  bin2xml.py
#  Generic Binary File Decoder

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

#  Copyright  Brian Starkey 2013
#  email:     stark3y[AT]gmail.com
#    web:     http://usedbytes.com

from lxml import etree as ET
from pprint import pprint
import math, copy, struct, string, argparse, os

DEBUG = False
VERBOSE = False
SILENT = False

def debug(s):
    if (DEBUG):
        out(s)
        
def warn(s):
    if (VERBOSE):
        out("WARNING: " + s)
        
def err(s):
    out("ERROR: " + s)

def out(s):
    if (not SILENT):
        print(s)

def parseDecHex(s):
    try:
        try:
            return int(s)
        except ValueError:
            return int(s, 16)
    except:
        return s 

class valueParser():
    
    def __init__(self, format):
        self.format = format
        self.value = ''
    
    # return True if the given text is parsed using self.format
    # sets self.value to a packed version of text using self.format
    def parseValue(self, text):
        self.value = ''
        # Special case, take the tag value literally
        if (self.format == 's'):
            self.format = 'c'
            self.value = text
            return True
        else :
            # Generate the appropriate list of values and corresponding
            # format string
            vlist = text.split()
            
            # these will be put back later
            sformat = self.format.lstrip('@=<>!')
            
            if (len(vlist) % len(sformat)):
                err("Invalid format ('" + self.format + "') for number of values (" + str(len(vlist)) + ")")
                return False
            elif (len(sformat) == 1):
                allow_stretching = True
                # repeat the format string to the required length
                sformat = sformat * (len(vlist) / len(sformat))
            else:
                allow_stretching = False
            
            i = 0
            debug("sformat: " + sformat)
            for v in vlist:
                debug("v: " + v + ", i: " + str(i) + ", sformat[i]: " + sformat[i])
                if (sformat[i] == 'c'):
                    # character format
                    # try to interpret this item as a number <= 256 (in decimal or hex)
                    numeric = parseDecHex(v)
                    if (isinstance(numeric, int)):
                        vlist[i] = chr(numeric)
                    elif (len(v) > 1):
                        # we have a string, so treat each letter as a separate item
                        if (allow_stretching):
                            vlist.insert(i+1, v[1:])
                            vlist[i] = v[0]
                            sformat = sformat[0:i+1] + 'c' + sformat[i+1:]
                        else:
                            err("Got string value: '" + v + "' for 'c' format, and stretching is not possible.")
                            return False
                else:
                    # we have a numeric format, so try to convert the item into numeric
                    vlist[i] = parseDecHex(v)
                i = i + 1
            
            if (self.format[0] in '@=<>!'):
                sformat = self.format[0] + sformat
                
            debug("using format: " + sformat + ", vlist:")
            if (DEBUG):
                pprint(vlist)
                
            # now we have a format string, and a correct list of values
            # use pack to generate a string of bytes
            self.value = struct.pack(sformat, *vlist)
            self.length = len(self.value)
            return True

class field():
    def __init__(self, et):
        # Populates the name, length and format fields.
        # If a value is defined (in the tag), store it in a corresponding
        # string of bytes so that it can later be compared to the input data
        try:
            self.name = et.attrib['name']
        except KeyError:
            raise KeyError("'name' is a required attribute for all fields")
        
        if (et.attrib.has_key('length')):
            self.length = parseDecHex(et.attrib['length'])
        else:
            self.length = ''
        
        if (et.attrib.has_key('format')):
            self.format = et.attrib['format']
        else:
            self.format = 'c'

        if (et.attrib.has_key('preferhex') and (et.attrib['preferhex'].lower() == 'yes')):
            self.preferhex = True
        else:
            self.preferhex = False

        self.value = ''
        self.possible_values = {}
        vparser = valueParser(self.format)
        
        self.allow_other_values = True
        
        # et has some children
        if (len(list(et))):
            i = 0
            for v in et.iter('value'):
                self.allow_other_values = False
                if not 'name' in v.keys():
                    raise ValueError("A name is required for all value definitions.")
                if (vparser.parseValue(v.text)):
                    self.possible_values[vparser.value] = v.attrib['name']
                    self.format = vparser.format
                else:
                    raise ValueError("Error whilst parsing value '" + et.text + "' with format '" + self.format + "'")
            for v in et.iter('allowothers'):
                self.allow_other_values = True
        
        # No value yet
        # Create a string of bytes from tag value
        if ((not len(self.possible_values)) and (et.text)):
            if (vparser.parseValue(et.text)):
                self.possible_values[vparser.value] = ''
                self.format = vparser.format
                self.allow_other_values = False
            else:
                raise ValueError("Error whilst parsing value '" + et.text + "' with format '" + self.format + "'")
        
        if (len(self.possible_values.keys())):
            lengths = set([len(k) for k in self.possible_values.keys()])
            if len(lengths) > 1:
                raise ValueError("All defined values must have the same length.")
            if (self.length != list(lengths)[0]):
                warn("Field '" + self.name + "': Length mismatch. Expected " +
                str(self.length) + " but got " + str(list(lengths)[0]))
            self.length = list(lengths)[0]
        #elif ((not self.length) and self.format):
        #    self.length = struct.calcsize(self.format)
        
        debug("self.value: " + self.value + ", self.length: " + str(self.length) + ", self.format: " + self.format)
                
    def hasSetValue(self):
        if (len(self.possible_values) > 0):
            return True
        else:
            return False

    def matchValue(self, buf):
        for k in self.possible_values.keys():
            if (k == buf):
                return True
        
        if (self.allow_other_values):
            return True
        else:
            return False

    def toString(self):
        if (self.value):
            return self.valToString(self.value)
        else:
            s = ''
            for k in self.possible_values.keys():
                s = s + self.valToString(k) + '\n'
            return s

    def valToString(self, value):
        s = ''
        if (self.preferhex):
            for item in self.unpackValue(value):
                s = s + hex(item) + ''
        elif (self.format.count('c') == len(self.format)):
            if (all(ord(c) < 127 and c in string.printable[0:-2] for c in value)):
                s = self.value
            else:
                for c in value:
                    s = s + hex(ord(c)) + ' '
        else :
            s = str(list(self.unpackValue(value)))
        if ((value in self.possible_values.keys()) and len(self.possible_values[value])):
            s = s + ' = ' + self.possible_values[value]
        return s
                    
    
    def printOut(self):
        out('Field: ' + self.name + ' | Length: ' + str(self.length) + 'B \n')
        out(self.toString)
        
    def printOut(self):
        pprint(self.attrib)
        out("Value: ")
        pprint(self.value)
    
    def unpackValue(self, value = None):
        if (not value):
            if (self.value):
                value = self.value
            else:
                return []
        
        if (self.length % struct.calcsize(self.format)):
            raise ValueError("Format '" + self.format + "' for field '" + self.name +
            "' is incompatible with length '" + str(self.length) + "'")
        else:
            return list(struct.unpack(self.format * (self.length/struct.calcsize(self.format)),
            value))


    def knownLength(self):
        if (isinstance(self.length, int)):
            return True
        else:
            return False
    
    def toElementTree(self):
        fnode = ET.Element('field')
        fnode.attrib['name'] = self.name
        if (self.length):
            fnode.attrib['length'] = str(self.length)
        if (self.format):
            fnode.attrib['format'] = self.format
            
        fnode.text = self.toString()
        return fnode
        
        
    def parse(self, stream):
        if not (self.knownLength()):
            return False;
        
        buf = stream[0 : self.length]
        if (self.matchValue(buf)):
            self.value = buf
            return True
        else:
            return False


class packetFragment():

    def __init__(self, data):
        self.length = len(data)
        if (self.length > 255):
            self.value = data[0:255]
        else:
            self.value = data
    
    def toElementTree(self):
        pnode = ET.Element('packet')
        pnode.attrib['name'] = "Fragment"
        pnode.attrib['length'] = str(len(self.value))
        pnode.attrib['numfields'] = "1"
        fnode = ET.Element('field')
        fnode.attrib['name'] = "data"
        fnode.attrib['format'] = 'c'
        if (self.length != len(self.value)):
            fnode.attrib['length'] = "Truncated"
        else:
            fnode.attrib['length'] = str(self.length)
        
        fnode.text = ''
        for c in self.value:
            fnode.text = fnode.text + hex(ord(c)) + ' '
        pnode.append(fnode)
        return pnode

class packet():

    def __init__(self, et):
        try:
            self.name = et.attrib['name']
        except KeyError:
            raise KeyError("A name is required for a packet type")
        
        self.fields = []
        for f in et.iter('field'):
            try:
                self.fields.append(field(f))
            except:
                out("Problem parsing packet format : '" + self.name + "'" )
                out("Field '" + f.attrib['name'] + "'")
                raise

    def toString(self):
        s = '|'
        for f in self.fields:
            s = s + f.name + ': ' + str(f.length) + '|'
        return s
        
    def printOut(self):
        out("Packet type '" + self.name + "':")
        for f in self.fields:
            f.printOut()

    def getField(self, fieldName):
        for f in self.fields:
            if (f.name == fieldName):
                return f
        raise KeyError("Field '" + fieldName + "' not found")

    def getFieldValue(self, fieldName):
        for f in self.fields:
            if (f.name == fieldName):
                vl = f.unpackValue()
                if (len(vl) > 1):
                    return vl
                else:
                    return parseDecHex(vl[0])

    def toElementTree(self):
        pnode = ET.Element('packet')
        pnode.attrib['name'] = self.name
        pnode.attrib['length'] = str(self.length)
        pnode.attrib['numfields'] = str(len(self.fields))
        for f in self.fields:
            pnode.append(f.toElementTree())
        return pnode
    
    def parse(self, stream):
        # p is the new packet we are attempting to construct
        p = copy.deepcopy(self)
        spos = 0
        i = 0
        for f in p.fields:
            
            # figure out field length
            if not (f.knownLength()):
                s = f.length
                if (s == ''):
                    if (i == (len(p.fields) - 1)):
                        # this is the last field, use up the rest of the buffer
                        f.length = len(stream) - spos
                    elif (p.fields[i + 1].hasSetValue()):
                        # we can try to terminate on the next field
                        nextField = p.fields[i + 1]
                        for j in range(spos, len(stream)):
                            if (nextField.parse(stream[j:])):
                                f.length = j - spos
                                break
                        if (f.length == ''):
                            # no match
                            raise ValueError("Unable to resolve a length for field '" + f.name + "'")
                            return False
                    else:
                        # there is no way we can figure it out
                        raise ValueError("Unable to resolve a length for field '" + f.name + "'")
                else: 
                    # might be a variable            
                    fieldName = s.lstrip('$')
                    try:
                        v = p.getFieldValue(fieldName)
                        if (isinstance(v, int)):
                            f.length = v
                        else:
                            raise TypeError("Specified value for length ('" + fieldName + "') is non-integer")
                    except:    
                        out("Unable to resolve a length for field '" + f.name + "'")
                        # why not?
                        raise

            debug("Length for '" + f.name + "' resolved as " + str(f.length))

            if (f.parse(stream[spos:])):
                spos = spos + f.length
            else:
                debug("Failed on field " + f.name)
                return False
            
            if (DEBUG):
                out("Final value for field '" + f.name + "'")
                pprint(f.toString())
                
            i = i + 1
        
        p.length = 0
        for f in p.fields:
            p.length = p.length + f.length
        
        return p

class templateList():
        
    def __init__(self, et):
        root = et.getroot()
        if (root.attrib.has_key('name')):
            self.name = root.attrib['name']
        else:
            self.name = "unnamed"
        self.filename = ''
        self.templates = []
        for pt in root.iter('template'):
            self.templates.append(packet(pt))
            out("Loaded Template: " + self.templates[-1].name)
    
    def parseFile(self, filename):
        self.filename = filename
        fp = open(filename, 'rb')
        # read whole file into memory... might be very bad!
        out("Loading file '" + filename + "'...")
        data = fp.read()
        out("Done!")
        fp.close()
        out("Processing...")
        return self.parse(data)

    def toElementTree(self, packets = ''):
        if (packets == ''):
            packets = self.templates
        root = ET.Element('root')
        root.attrib['name'] = self.name
        if (self.filename):
            root.attrib['filename'] = self.filename
            
        for p in packets:
            root.append(p.toElementTree())
        return root

    def parse(self, data):
        global VERBOSE
        
        pos = 0
        if (len(self.templates) == 0):
            out("No templates loaded.")
            return False
        parsed = []
        p = False
        i = 0
        scanning = False
        skipped = 0
        corrupt = 0
        while (pos < len(data)):
            for i in range(0, len(self.templates)):
                debug("Try template " + str(i))
                p = self.templates[i].parse(data[pos:])
                if (p):
                    if (scanning and skipped):
                        warn("Skipped " + str(skipped) + " bytes.")
                        parsed.append(packetFragment(data[pos - skipped: pos]))
                        skipped = 0
                    if (VERBOSE):
                        out("Got packet of type '" + p.name + "', Length: " + str(p.length))
                    parsed.append(p)
                    pos = pos + p.length
                    scanning = False
                    #out("Breaking out")
                    break;
            #out("Next")
            if (p == False):
                if not (scanning):
                    warn("Corrupt, unrecognised or partial packet")
                    scanning = True
                    corrupt = corrupt + 1
                skipped = skipped + 1
                pos = pos + 1
        
        out(str(corrupt) + " corrupt, unrecognised or incomplete packets.")
        if (len(parsed)):
            out("Parsed " + str(len(parsed)) + " packets.")
            return parsed
        else:
            return False

# Command line arguments
parser = argparse.ArgumentParser('Process the binary input file according to the packet formats defined in the XML file')
parser.add_argument('template', metavar='template', type=str, nargs=1, help='the XML format file to use')
parser.add_argument('-i', metavar='input_file', dest='input_filename', type=str, nargs=1, help='the binary file to process')
parser.add_argument('-o', metavar='output_file', dest='output_filename', type=str, nargs=1, help='XML file to write parsed data to')
parser.add_argument('-s', metavar='stylesheet', dest='stylesheet', default=[os.path.realpath(os.curdir) + "/default.xsl"], type=str, nargs=1, help='XSL stylesheet to use for the output')
parser.add_argument('-v', default=False, action='store_true', dest='verbose', help='Increase output')
parser.add_argument('-d', default=False, action='store_true', dest='debug', help='Debug')
parser.add_argument('-t --transform', default=False, action='store_true', dest='transform', help='Perform an XSLT transform on the data before outputting')
arguments = parser.parse_args();

# Output level flags
if (DEBUG):
    pprint(arguments)
VERBOSE = arguments.verbose
DEBUG = arguments.debug
SILENT = arguments.input_filename and not arguments.output_filename

# Build template list
template_file = open(arguments.template[0], 'r')
template_tree = ET.parse(template_file)
template_file.close()
template_list = templateList(template_tree)

if (arguments.input_filename):
    processed_packets = template_list.parseFile(arguments.input_filename[0])
    
    if (processed_packets) :          
    
        parsed_root = template_list.toElementTree(processed_packets)
        parsed_root.attrib['style_dir'] = os.path.dirname(os.path.abspath(arguments.stylesheet[0]))
        parsed_root.attrib['filename'] = os.path.abspath(arguments.input_filename[0])
        parsed_tree = ET.ElementTree(parsed_root)
        
        if (arguments.transform):
            print(arguments.stylesheet[0])
            xsl_file = open(arguments.stylesheet[0], 'r')
            xslt = ET.XSLT(ET.parse(xsl_file))
            xsl_file.close()
            
            output = xslt(parsed_tree)
        
        elif (arguments.stylesheet):
            parsed_root.addprevious(ET.PI('xml-stylesheet', 'type="text/xsl" href="' + arguments.stylesheet[0] + '"'))
            output = parsed_tree
        
        if not (arguments.output_filename):
            print ET.tostring(output, pretty_print = True)
        else:
            output_file = open(arguments.output_filename[0], 'w')
            if not (arguments.transform):
                output.write(output_file, pretty_print = True, xml_declaration = True)
            else:
                output.write(output_file, pretty_print = True)
            output_file.close()
            out("Written to '" + arguments.output_filename[0] + "'")
    else:
        out("Nothing Read.")
    
