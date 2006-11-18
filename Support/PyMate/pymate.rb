require "#{ENV["TM_SUPPORT_PATH"]}/lib/scriptmate"

$SCRIPTMATE_VERSION = "$Revision$"

class PythonScript < UserScript
  @@args = ['-u']
  def executable
    @hashbang || ENV['TM_PYTHON'] || 'python'
  end
  def version_string
    res = %x{#{executable} -V 2>&1 }.chomp
    res + " (#{executable})"
  end
end

class PyMate < ScriptMate
  @@lang = "Python"
end

PyMate.new(PythonScript.new).emit_html
