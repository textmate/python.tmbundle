# rubocop: disable Style/HashSyntax

# -- Imports -------------------------------------------------------------------

require ENV['TM_SUPPORT_PATH'] + '/lib/exit_codes'
require ENV['TM_SUPPORT_PATH'] + '/lib/progress'
require ENV['TM_SUPPORT_PATH'] + '/lib/tm/detach'
require ENV['TM_SUPPORT_PATH'] + '/lib/tm/save_current_document'

# -- Module --------------------------------------------------------------------

# This module allows us to reformat a file via YAPF.
module YAPF
  class << self
    # This function reformats the current TextMate document using YAPF.
    #
    # It works both on saved and unsaved files:
    #
    # 1. In the case of an unsaved files this method will stall until YAPF
    #    fixed the file. While this process takes place the method displays a
    #    progress bar.
    #
    # 2. If the current document is a file saved somewhere on your disk, then
    #    the method will not wait until YAPF is finished. Instead it will run
    #    YAPF in the background. This has the advantage, that you can still
    #    work inside TextMate, while YAPF works on the document.
    def reformat
      unsaved_file = true unless ENV['TM_FILEPATH']
      TextMate.save_if_untitled('py')
      format_file(locate_yapf, unsaved_file)
    end

    private

    def locate_yapf
      Dir.chdir(ENV['TM_PROJECT_DIRECTORY'] ||
                File.dirname(ENV['TM_FILEPATH'].to_s))
      yapf = ENV['TM_YAPF'] || 'yapf'
      return yapf if File.executable?(`which #{yapf}`.rstrip)
      TextMate.exit_show_tool_tip(
        'Could not locate YAPF. Please make sure that you set TM_YAPF ' \
        "correctly.\nTM_YAPF: “#{ENV['TM_YAPF']}”"
      )
    end

    def format_file(yapf, unsaved_file)
      style = ENV['TM_YAPF_STYLE'] || 'pep8'
      filepath = ENV['TM_FILEPATH']
      command = "#{yapf} -i --style=#{style} \"$TM_FILEPATH\" 2>&1"
      error_message = "YAPF was not able to reformat the file: \n\n"
      if unsaved_file
        format_unsaved(command, error_message, filepath)
      else
        format_saved(command, error_message, filepath)
      end
    end

    def format_unsaved(yapf_command, error_message, filepath)
      output, success = TextMate.call_with_progress(
        :title => '🐍 YAPF', :summary => 'Reformatting File'
      ) do
        [`#{yapf_command}`, $CHILD_STATUS.success?]
      end
      TextMate.exit_show_tool_tip(error_message + output) unless success
      TextMate::UI.tool_tip(output) unless output.empty?
      TextMate.exit_replace_document(File.read(filepath))
    end

    def format_saved(yapf_command, error_message, filepath)
      TextMate.detach do
        output = `#{yapf_command}`
        if $CHILD_STATUS.success?
          output = (":\n\n" + output) unless output.empty?
          message = "✨ Reformatted “#{File.basename(filepath)}”#{output}"
          TextMate::UI.tool_tip(message)
        else
          TextMate::UI.tool_tip(error_message + output)
        end
      end
    end
  end
end
