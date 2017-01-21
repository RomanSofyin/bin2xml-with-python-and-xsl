<?xml version="1.0"?>
<!-- 
     default.xsl
     Default stylesheet for processing output from parse_binary 
     
     Copyright  Brian Starkey 2013
     email:     stark3y[AT]gmail.com
       web:     http://usedbytes.com
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template match="/root">
      <html>
          <head>
            <link href="{@style_dir}/default.css" rel="stylesheet" type="text/css"/>
          </head>
          
          <body>
            <h1><xsl:value-of select="@name"/></h1>
            <h2>File: <xsl:value-of select="@filename"/></h2>
    
            <xsl:for-each select="packet">
                <table class="packet">
                    <tr>
                        <th colspan="4" class="packet_header"><xsl:value-of select="@name"/> - <xsl:value-of select="@length"/> Bytes</th>
                    </tr>
                    <tr>
                        <td class="field_header">Name</td>
                        <td class="field_header">Length</td>
                        <td class="field_header">Format</td>
                        <td class="field_header">Data</td>
                    </tr>
                    
                    <xsl:for-each select="field">
                        <tr class="field">
                            <td class="field_name"><xsl:value-of select="@name"/></td>
                            <td class="field_length"><xsl:value-of select="@length"/></td>
                            <td class="field_format"><xsl:value-of select="@format"/></td>
                            <td class="field_data"><xsl:value-of select="."/></td>
                        </tr>
                    </xsl:for-each>
                    
                </table>
                <br/>
            </xsl:for-each>
          
          </body>  
      </html>
    </xsl:template>

</xsl:stylesheet>
