require "#{ENV["TM_SUPPORT_PATH"]}/lib/scriptmate"

$SCRIPTMATE_VERSION = "$Revision$"

class PythonScript < UserScript
  @@execmatch = "python(?:\d+\.\d+)?"
  @@execargs = ['-u']
  def executable
    @arg0 || ENV['TM_PYTHON'] || 'python'
  end
  def version_string
    res = %x{#{executable} -V 2>&1 }.chomp
    res + " (#{executable})"
  end
end

class PyMate < ScriptMate
  @@matename = "PyMate"
  @@langname = "Python"
end

PyMate.new(PythonScript.new).emit_html
