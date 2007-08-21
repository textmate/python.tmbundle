require "#{ENV["TM_SUPPORT_PATH"]}/lib/scriptmate"
require "pathname"

$SCRIPTMATE_VERSION = "$Revision$"

class PythonScript < UserScript
  def lang; "Python" end
  def executable; @hashbang || ENV['TM_PYTHON'] || 'python' end
  def args; ['-u'] end
  def version_string
    res = %x{#{executable} -V 2>&1 }.chomp
    res + " (#{executable})"
  end
  def test_script?
    @path    =~ /(?:\b|_)(?:test)(?:\b|_)/ or
    @content =~ /\import\b.+(?:unittest)/
  end
  def filter_cmd(cmd)
    pymatepath = Pathname.new(ENV["TM_BUNDLE_SUPPORT"]) +\
                  Pathname.new("PyMate")
    return ["export PYTHONPATH=\"#{pymatepath}:$PYTHONPATH\";"] + cmd
  end
end

# we inherit from scriptmate just to change the classname to PyMate.
class PyMate < ScriptMate
  def filter_stderr(str)
    if @command.test_script? and str =~ /\A[EF]+\Z/
      return htmlize(str).gsub(/[EF]+/, "<span style=\"color: red\"><b>\\&</b></span>") +
            "<br style=\"display: none\"/>"
    elsif @command.test_script? and str =~ /\A\.\Z/
      return htmlize(str).gsub(/\./, "<span style=\"color: green\"><b>\\&</b></span>") +
            "<br style=\"display: none\"/>"
    elsif @command.test_script?
        return ( str.map do |line|
          if line =~ /^(\s+)File (\S.+), line (\d+), in (.*)/
            indent, file, line, method = $1, $2, $3, $4
            url, display_name = '', 'untitled document';
            unless file == "-"
              indent += " " if file.sub!(/^"(.*)"/,'\1')
              url = '&amp;url=file://' + e_url(file)
              display_name = File.basename(file)
            end
            "#{indent}<a class='near' href='txmt://open?line=#{line + url}'>" +
            (method ? "method #{CGI::escapeHTML method}" : '<em>at top level</em>') +
            "</a> in <strong>#{CGI::escapeHTML display_name}</strong> at line #{line}<br/>"
          elsif line =~ /^FAILED(.*)/
            "<span style=\"color: red\"><b>FAILED#{$1}</b></span><br/>"
          elsif line =~ /^OK(.*)/
            "<span style=\"color: red\"><b>OK#{$1}</b></span><br/>"
          else
            htmlize(line)
          end
        end.join )
    else
      "<span style='color: red'>#{htmlize str}</span>".gsub(/\<br\>/, "<br>\n")
    end
  end
end


script = PythonScript.new(STDIN.read)
PyMate.new(script).emit_html
