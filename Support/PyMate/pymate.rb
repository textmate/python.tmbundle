require "#{ENV["TM_SUPPORT_PATH"]}/lib/scriptmate"
require "pathname"
$KCODE = 'u'
require 'jcode'

STDOUT.sync = true

$SCRIPTMATE_VERSION = "$Revision$"

class PythonScript < UserScript
  def lang; "Python" end
  def executable; @hashbang || ENV['TM_PYTHON'] || 'python' end
  def args;
    if @path != "-"
      ['-u', "-c \"import tmhooks, sys; del sys.argv[0]; __file__ = sys.argv[0]; del sys, tmhooks; execfile(__file__)\""]
    else
      ['-u', "-c #{e_sh "import tmhooks, sys; del tmhooks,sys;\n" + @content}"]
    end
  end
  def version_string
    res = %x{#{executable} -V 2>&1 }.chomp
    res + " (#{executable})"
  end
  def test_script?
    @path    =~ /(?:\b|_)(?:test)(?:\b|_)/ or
    @content =~ /\bimport\b.+(?:unittest)/
  end
  def filter_cmd(cmd)
    pymatepath = Pathname.new(ENV["TM_BUNDLE_SUPPORT"]) +\
                  Pathname.new("PyMate")
    return ["export PYTHONPATH=\"#{pymatepath}:$PYTHONPATH\";"] + cmd
  end
end

class PyMate < ScriptMate
  def filter_stderr(str)
    if @command.test_script?
      (str.map do |line|
        if line =~ /\A[F]\Z/
          "<span style=\"color: red\"><b>#{line.strip}</b></span><br>"
        elsif line =~ /\A\.\Z/
          "<span style=\"color: green\"><b>#{line.strip}</b></span><br>"
        elsif line =~ /\A(FAILED.*)\Z/
          "<span style=\"color: red;\"><b>#{$1}</b></span><br/>\n"
        elsif line =~ /\A(OK.*)\Z/
          "<span style=\"color: green\"><b>#{$1}</b></span><br/>"
        elsif line =~ /^(\s+)File "(.+)", line (\d+), in (.*)/
          indent, file, line, method = $1, $2, $3, $4
          url, display_name = '', 'untitled';
          unless file == "-" or file == "<stdin>"
            indent += " " if file.sub!(/^"(.*)"/,'\1')
            url = '&amp;url=file://' + e_url(file)
            display_name = File.basename(file)
          end
          "#{htmlize(indent)}<a class='near' href='txmt://open?line=#{line + url}'>" +
            (method ? "method #{CGI::escapeHTML method}" : '<em>at top level</em>') +
            "</a> in <strong>#{CGI::escapeHTML display_name}</strong> at line #{line}<br/>"
        else
          htmlize(line)
        end
      end).join.gsub(/\<br\/?\>/, "<br>\n")
    else
      "<span style='color: red'>#{htmlize str}</span>"
    end
  end
end

script = PythonScript.new(STDIN.read, false)
PyMate.new(script).emit_html
