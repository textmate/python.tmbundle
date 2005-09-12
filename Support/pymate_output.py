# encoding: utf-8

# copyright (c) Domenico Carbotta, 2005
# with enhancements and precious input by Brad Miller and Jeroen van der Ham
# this script is released under the GNU General Public License


preface = '''
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>PyMate</title>
    <style type="text/css">
    <!--
    body {
    	background-color: #D8E2F1;
    	margin: 0;
    }
    div {
    	border-style: dotted;
    	border-width: 1px 0;
    	border-color: #666;
    	margin: 10px 0;
    	padding: 10px;
    }
    p { margin: 0; padding: 2px 0; }
    
    div#script_output {
    	background-color: #C9D9F0;
    }
    
    p#preface strong { font-size: 11pt; }
    p#preface small { font-size: 9pt; }
    
    pre#output {
    	padding: 0;
    	margin: 0;
    	line-height: 1.5;
    	font-family: Monaco;
    	font-size: 8pt;
    }

    pre#output strong {
    	/* used for messages */
    	font-weight: normal;
    	color: #28569C;
    }
    pre#output em {
    	/* used for stderr */
    	font-style: normal;
    	color: #FF5600;
    }

    div#exception_report {
        background-color: #B8CFF0;
    }
    
    p#exception { font-size: 9pt; }
    p#exception strong { color: rgb(220,0,0); }
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
    
    -->
    </style>
    </head>
    <body>
    <div id="script_output">
    
    <p id="preface">
        <strong>%s</strong><br><br>
        <small>
            Please remember that PyMate is still in an early beta stage...
            Send all your bug reports to <a
            href="mailto:domenico.carbotta@gmail.com">the author</a> :)
            <br>
            The regular Python interpreter can be invoked using
                &#x2318;&#x21E7;R.
        </small>
        <br><br>
    </p>
    <pre id="output"><strong>&gt;&gt;&gt %s</strong>
'''
# % (version, short_filename)

exception_preface = '''</pre></div>
<div id="exception_report">
<p id="exception"><strong>%s</strong>%s</p>
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

syntax = '''</pre></div>
<div id="exception_report">
<p id="exception"><strong>%s</strong>%s</p>
</div>
</body>
</html>
''' # % (exception_name, exception_arguments)

normal_end = '''</pre>
</div>
</body>
</html>
'''