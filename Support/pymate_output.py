# encoding: utf-8

# copyright (c) Domenico Carbotta, 2005
# with enhancements and precious input by Brad Miller and Jeroen van der Ham
# this script is released under the GNU General Public License


preface = '''<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>PyMate</title>
<style type="text/css">
<!--
/* the script that shows/hides stderr relies upon the ordering
   of the first three rules. */

/* <don't touch> */

    span.stderr {
        display: inline;
    	color: #F50;
    }

    span.stderr_notice {
        display: none;
    	color: #F50;
    }

    pre#output hr {
        display: block;
        border: 0;
        border-top: 1px dotted #F50;
    }

/* </don't touch> */

body {
	background-color: #D8E2F1;
	margin: 0;
}

div#menu {
    font-size: 7pt;
    font-weight: bold;
    border-bottom: 1px dotted #F50;
    float: right;
    padding: 0px;
    margin: 2px;
    text-align: right;
    cursor: hand;
}

div#script_output, div#report {
	border-style: dotted;
	border-width: 1px 0;
	border-color: #666;
	margin: 10px 0;
	padding: 10px;
}

div#script_output {
	background-color: #C9D9F0;
}

p { margin: 0; padding: 2px 0; }
p#preface strong { font-size: 11pt; }
p#preface small { font-size: 9pt; }

pre#output {
	padding: 0;
	margin: 0;
	margin-bottom: -12pt;
	line-height: 1.5;
	font-family: Monaco;
	font-size: 8pt;
}

pre#output strong {
	/* used for messages */
	font-weight: normal;
	color: #28569C;
}


div#report {
    background-color: #B8CFF0;
}

p#header { font-size: 9pt; }
p#header strong { color: rgb(220,0,0); }
p#header em { color: #28569C; font-weight: bold; font-style: normal; }
p#traceback { font-size: 8pt; }

table { margin: 0 40px; padding: 0; }

td {
	margin: 0;
	padding: 2px;
	font-size: 9pt;
}

abbr { border-bottom: 1px dotted; font-weight: bold; }
a, a.near { color: rgb(30,90,135); }
a.far { color: #B73D00; }

.suppress { display: none; }

div.solid_banner {
    background-color: #F50;
    color: white;
    border: 1px dotted white;
    font-family: sans-serif;
    width: 50%%;
    padding: 5px;
}

-->
</style>
<script type="text/javascript">
<!--

var STDERR = 0;
var NOTICE = 1;
var HR = 2;

function setStyle(selector, property_name, property_value) {
    rule = document.styleSheets[0].rules.item(selector);
    rule.style.setProperty(property_name, property_value, '!important');
}

function showStdErr() {
    setStyle(STDERR, 'display', 'inline');
    setStyle(NOTICE, 'display', 'none');
    setStyle(HR, 'display', 'block');
}

function hideStdErr() {
    setStyle(STDERR, 'display', 'none');
    setStyle(NOTICE, 'display', 'inline');
    setStyle(HR, 'display', 'none');
}

// -->
</script>
</head>
<body>
<div id="script_output">

<p id="preface">
    <div id="menu">
        <span class="stderr" onclick="hideStdErr();">HIDE STDERR</span>
        <span class="stderr_notice" onclick="showStdErr();">SHOW STDERR</span>
    </div>
    <strong>%s</strong><br><br>
    <small>
        For comments contact <a
        href="mailto:domenico.carbotta@gmail.com?subject=%s"
        >the author</a>.
        <br>
        The regular Python interpreter can be invoked using
            &#x2318;&#x21E7;R.
    </small>
    <br><br>
</p>
<pre id="output"><strong>&gt;&gt;&gt; %s</strong>

<div class="suppress">'''
# % (version_string, __version__, short_filename)

std_preface = '''
<div id="report">
<p id="header"><em>%s</em> %s</p>
''' # % (status, message)

exception_preface = '''
<div id="report">
<p id="header"><strong>%s</strong>%s</p>
<p id="traceback">Traceback:</p>
<table border="0" cellspacing="0" cellpadding="0">
''' # % (exception_name, exception_arguments)

tbitem_near = '''
    <tr>
        <td>function
            <a class="near" title="in %(filename)s"
                href="txmt://open?url=file://%(filename)s&line=%(lineno)d">
                %(func_name)s
            </a>
        </td>
        <td>
            in <abbr title="%(filename)s">%(short_filename)s</abbr>
            at line %(lineno)d
        </td>
    </tr>
''' # % {func_name, filename, short_filename, lineno}

tbitem_far = '''
    <tr>
        <td>function
            <a class="far"
                href="txmt://open?url=file://%(filename)s&line=%(lineno)d">
                %(func_name)s
                \xe2\x8e\x8b
            </a>
        </td>
        <td>
            in <abbr title="%(filename)s">%(short_filename)s</abbr>
            at line %(lineno)d
        </td>
    </tr>
''' # % {func_name, filename, short_filename, lineno}

tbitem_binary = '''
    <tr>
        <td>
            function %(func_name)s
        </td>
        <td>
            in <abbr title="%(filename)s">
                %(short_filename)s</abbr>
            at line %(lineno)d (file does not exist)
        </td>
    </tr>
''' # % {func_name, filename, short_filename, lineno}

exception_end = '''</table>
</div>
</body>
</html>
'''

syntax = '''
<div id="report">
<p id="header"><strong>%s</strong>%s</p>
</div>
</body>
</html>
''' # % (exception_name, exception_arguments)

redraw_trick = '''<span style="visibility: hidden;"><span
class="stderr">forcing redraw!!!</span> don't remove</span>'''