# Print an optspec for argparse to handle cmd's options that are independent of any subcommand.
function __fish_soundcraft_cli_global_optspecs
    string join \n h/help V/version
end

function __fish_soundcraft_cli_needs_command
    # Figure out if the current invocation already has a command.
    set -l cmd (commandline -opc)
    set -e cmd[1]
    argparse -s (__fish_soundcraft_cli_global_optspecs) -- $cmd 2>/dev/null
    or return
    if set -q argv[1]
        # Also print the command, so this can be used to figure out what it is.
        echo $argv[1]
        return 1
    end
    return 0
end

function __fish_soundcraft_cli_using_subcommand
    set -l cmd (__fish_soundcraft_cli_needs_command)
    test -z "$cmd"
    and return 1
    contains -- $cmd[1] $argv
end

complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -s h -l help -d 'Print help'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -s V -l version -d 'Print version'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "info" -d 'Print an audio file\'s format as JSON, or a .scraft session\'s summary'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "convert" -d 'Convert an audio file: resample, change the bit depth, normalize'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "run" -d 'Run engine commands on a new, demo or saved session'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "script" -d 'Run a file of engine commands, one `ID JSON` per line'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "commands" -d 'List the engine commands'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "describe" -d 'Print one engine command\'s details as JSON'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "app" -d 'Call a running app\'s control channel'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "mcp" -d 'Serve MCP on stdin and stdout'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "parity" -d 'Print the parity report (markdown)'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "plugins" -d 'List the built-in plugins'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_needs_command" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand info" -l compact -d 'One line of JSON instead of pretty-printed (a .scraft summary is text and ignores it)'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand info" -s h -l help -d 'Print help'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -l bit-depth -d 'The output\'s bit depth' -r -f -a "16\t''
24\t''
32f\t''"
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -l rate -d 'Resample to this sample rate' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -l normalize -d 'Normalize the peak to -0.1 dBFS'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -l dither -d 'Always dither'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -l no-dither -d 'Never dither'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -l in-place -d 'Allow an <OUT> that is the <IN> file, replacing the original'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand convert" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l cmd -d 'An engine command, with its JSON parameters after `=` (default {}); repeat for several, run in order' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l in -d 'Open this session first' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l bounce -d 'Bounce the mix to this file at the end; without --start and --end, the whole session' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l start -d 'Where the bounce starts: seconds (12.5) or a time string' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l end -d 'Where the bounce ends: seconds (12.5) or a time string' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l save -d 'Save the session to this file at the end, replacing it' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l demo -l sample -d 'Start from the demo session'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l inspect -d 'Print the session as JSON at the end'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l compact -d 'Print the --inspect JSON on one line instead of pretty-printed'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -l in-place -d 'Allow a --save that is the --in session, replacing the original'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand run" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l in -d 'Open this session first' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l bounce -d 'Bounce the mix to this file at the end; without --start and --end, the whole session' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l start -d 'Where the bounce starts: seconds (12.5) or a time string' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l end -d 'Where the bounce ends: seconds (12.5) or a time string' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l save -d 'Save the session to this file at the end, replacing it' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l keep-going -d 'Continue after command errors and finish requested output, then exit nonzero if any command failed. Malformed JSON stops immediately'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l demo -l sample -d 'Start from the demo session'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l inspect -d 'Print the session as JSON at the end'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l compact -d 'Print the --inspect JSON on one line instead of pretty-printed'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -l in-place -d 'Allow a --save that is the --in session, replacing the original'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand script" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand commands" -l json -d 'Print a JSON array of each command\'s details, as describe prints them'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand commands" -l compact -d 'One line of JSON instead of pretty-printed'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand commands" -s h -l help -d 'Print help'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand describe" -l compact -d 'One line of JSON instead of pretty-printed'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand describe" -s h -l help -d 'Print help'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand app" -l port -d 'The app\'s control port or host:port' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand app" -l compact -d 'One line of JSON instead of pretty-printed'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand app" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand mcp" -l connect -d 'Serve a running app\'s control channel at this port or host:port instead of an in-process engine; conflicts with --demo, which starts only that engine' -r
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand mcp" -l automation-read-root -d 'A folder the agent\'s commands may read from; repeat for several' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand mcp" -l automation-write-root -d 'A folder the agent\'s commands may write to; repeat for several' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand mcp" -l demo -d 'Start the in-process engine from the demo session'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand mcp" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand parity" -l write -d 'Write the report to this file instead' -r -F
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand parity" -s h -l help -d 'Print help'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand plugins" -s h -l help -d 'Print help'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "info" -d 'Print an audio file\'s format as JSON, or a .scraft session\'s summary'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "convert" -d 'Convert an audio file: resample, change the bit depth, normalize'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "run" -d 'Run engine commands on a new, demo or saved session'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "script" -d 'Run a file of engine commands, one `ID JSON` per line'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "commands" -d 'List the engine commands'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "describe" -d 'Print one engine command\'s details as JSON'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "app" -d 'Call a running app\'s control channel'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "mcp" -d 'Serve MCP on stdin and stdout'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "parity" -d 'Print the parity report (markdown)'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "plugins" -d 'List the built-in plugins'
complete -c soundcraft-cli -n "__fish_soundcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run script commands describe app mcp parity plugins help" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
