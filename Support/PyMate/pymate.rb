require "#{ENV["TM_SUPPORT_PATH"]}/lib/scriptmate"
require "pathname"

$SCRIPTMATE_VERSION = "$Revision$"

class PythonScript < UserScript
  def lang; "Python" end
  def filter_cmd(cmd)
    pymatepath = Pathname.new(ENV["TM_BUNDLE_SUPPORT"]) +\
                  Pathname.new("PyMate")
    return ["export PYTHONPATH=\"#{pymatepath}:$PYTHONPATH\";"] + cmd
  end
  def executable; @hashbang || ENV['TM_PYTHON'] || 'python' end
  def args; ['-u'] end
  def version_string
    res = %x{#{executable} -V 2>&1 }.chomp
    res + " (#{executable})"
  end
end

# we inherit from scriptmate just to change the classname to PyMate.
class PyMate < ScriptMate; end

script = PythonScript.new(STDIN.read)
PyMate.new(script).emit_html
