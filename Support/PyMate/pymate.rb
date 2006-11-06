require "#{ENV["TM_SUPPORT_PATH"]}/lib/escape"
require "#{ENV["TM_SUPPORT_PATH"]}/lib/web_preview"

require 'open3'
require 'cgi'
require 'fcntl'

$PYTHONMATE_VERSION = "$Revision$"

class UserScript
  def initialize
    @content = STDIN.read
    @arg0 = $1       if @content =~ /\A#!([^ \n]+\/python\b)/
    @args = $1.split if @content =~ /\A#!.*?\bpython[ \t]+(.*)$/

    if ENV.has_key? 'TM_FILEPATH' then
      @path = ENV['TM_FILEPATH']
      @display_name = File.basename(@path)
      # save file
      open(@path, "w") { |io| io.write @content }
    else
      @path = '-'
      @display_name = 'untitled'
    end
  end

  def python
    @arg0 || ENV['TM_PYTHON'] || 'python'
  end

  def python_version_string
    res = %x{ #{e_sh python} -c "import sys; print sys.version.split(' ')[0]" }.chomp
    res + " (#{python})"
  end

  def run
    rd, wr = IO.pipe
    rd.fcntl(Fcntl::F_SETFD, 1)
    ENV['TM_ERROR_FD'] = wr.to_i.to_s
    args = [ python, Array(@args), @path, ARGV.to_a ].flatten
    stdin, stdout, stderr = Open3.popen3(*args)
    Thread.new { stdin.write @content; stdin.close } unless ENV.has_key? 'TM_FILEPATH'
    wr.close
    [ stdout, stderr, rd ]
  end
  attr_reader :display_name, :path
end

error = ""
STDOUT.sync = true

script = UserScript.new

puts html_head(:window_title => "#{script.display_name} — PyMate", :page_title => 'PyMate', :sub_title => 'Python')
puts <<-HTML
	<div class="pythonmate">
		
		<div><!-- first box containing version info and script output -->
			<pre><strong>PyMate r#{$PYTHONMATE_VERSION[/\d+/]} running Python v#{script.python_version_string}</strong>
<strong>>>> #{script.display_name}</strong>

<div style="white-space: normal; -khtml-nbsp-mode: space; -khtml-line-break: after-white-space;"> <!-- Script output -->
HTML

stdout, stderr, stack_dump = script.run
descriptors = [ stdout, stderr, stack_dump ]

descriptors.each { |fd| fd.fcntl(Fcntl::F_SETFL, Fcntl::O_NONBLOCK) }
until descriptors.empty?
  select(descriptors).shift.each do |io|
    str = io.read
    if str.to_s.empty? then
      descriptors.delete io
      io.close
    elsif io == stdout then
      print htmlize(str)
    elsif io == stderr then
      print "<span style='color: red'>#{htmlize str}</span>"
    elsif io == stack_dump then
      error << str
    end
  end
end

puts '</div></pre></div>'
puts error
puts '<div id="exception_report" class="framed">Program exited.</div>'
puts '</div>'
puts '</body></html>'
