bin2xml - A Generic Binary File Parser
======================================
Copyright Brian Starkey 2013
  web: http://usedbytes.com/software/bin2xml
email: stark3y[AT]gmail.com

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

bin2xml is an attempt at a completely generic, configureable file parser,
mainly aimed at binary input data. It uses an XML definition file to attempt
to decode an input file into "packets", then wraps those up in XML structures 
for output. Optionally, it can use an XSL stylesheet to transform the XML 
before it gets output. By default, a generic "default.xsl" and "default.css"
style combination will be used, which generates the red tables shown on this
page.

The definition file contains one or more "templates", which define the data 
layout for a type of data packet. bin2xml will try each one of these templates 
in turn (in the order they appear in the template file), and if one of the 
templates matches, then the data will be parsed into it. A populated XML 
structure is then generated, which is the same as the template used, but fully 
populated with the input data. The format for the template file is described 
in full in writing_templates.txt.

bin2xml is written in Python, so it isn't going to break any records for sheer speed, however the advantage is it was easy to write (taking a few days) and is incredibly flexible.

    ./bin2xml.py -h
    usage: Process the binary input file according to the packet formats defined in 
the XML file
           [-h] [-i input_file] [-o output_file] [-s stylesheet] [-v] [-d]
           [-t --transform]
           template

           positional arguments:
               template        the XML format file to use

           optional arguments:
               -h, --help      show this help message and exit
               -i input_file   the binary file to process
               -o output_file  XML file to write parsed data to
               -s stylesheet   XSL stylesheet to use for the output
               -v              Increase output
               -d              Debug
               -t --transform  Perform an XSLT transform on the data before 
                               outputting

Broadly speaking, a bin2xml command will look something like this:
./bin2xml.py format_file.xml -i binary_data.log -t -o pretty_output.html


<sub><a target="_blank" href="https://paypal.me/e1adkarak0" rel="nofollow"><img src="https://www.paypalobjects.com/webstatic/mktg/Logo/pp-logo-100px.png" width="60" height="16" border="0" alt="PayPal Donation"></a></sub>
