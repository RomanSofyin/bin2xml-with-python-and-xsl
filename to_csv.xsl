<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" encoding="iso-8859-1"/>

<xsl:strip-space elements="*" />

    <xsl:template match="/root">

        <xsl:for-each select="packet">
            <xsl:for-each select="field">
                <xsl:if test="position() != last()">"<xsl:value-of select="normalize-space(.)"/>",    </xsl:if>
                <xsl:if test="position()  = last()">"<xsl:value-of select="normalize-space(.)"/>"<xsl:text>
                </xsl:text>
                </xsl:if>
            </xsl:for-each>
        </xsl:for-each>

    </xsl:template>

</xsl:stylesheet>
