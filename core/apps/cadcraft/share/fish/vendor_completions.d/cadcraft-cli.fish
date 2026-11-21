# Print an optspec for argparse to handle cmd's options that are independent of any subcommand.
function __fish_cadcraft_cli_global_optspecs
    string join \n h/help V/version
end

function __fish_cadcraft_cli_needs_command
    # Figure out if the current invocation already has a command.
    set -l cmd (commandline -opc)
    set -e cmd[1]
    argparse -s (__fish_cadcraft_cli_global_optspecs) -- $cmd 2>/dev/null
    or return
    if set -q argv[1]
        # Also print the command, so this can be used to figure out what it is.
        echo $argv[1]
        return 1
    end
    return 0
end

function __fish_cadcraft_cli_using_subcommand
    set -l cmd (__fish_cadcraft_cli_needs_command)
    test -z "$cmd"
    and return 1
    contains -- $cmd[1] $argv
end

complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -s h -l help -d 'Print help'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -s V -l version -d 'Print version'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "info" -d 'Print a drawing\'s summary as JSON'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "convert" -d 'Convert a drawing; OUT\'s extension picks the format (dxf, dwg, dwt, svg, png, pdf)'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "run" -d 'Open drawings (or start a new one), run scripts and commands in order, save or export the result'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "commands" -d 'Print the command catalog as JSON'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "mcp" -d 'Run the MCP server on stdio: a headless drawing session, or a bridge to the running app'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "perf" -d 'Time the engine on a synthetic N-entity drawing (default 200000), or the canvas display-list build of a drawing, zoomed in step by step'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "sample" -d 'Write a built-in sample drawing'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "roundtrip" -d 'Open each DXF/DWG, save it as DXF and DWG, reopen and compare; writes report.md and report.json'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_needs_command" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand info" -l compact -d 'One line of JSON instead of pretty-printed'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand info" -s h -l help -d 'Print help'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -l window -d 'Show this rectangle (drawing units, x0<x1, y0<y1), centred and scaled to fit the image without distortion. A negative x0 needs the `=` form: --window=-10,0,10,5' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -l view -d 'What part of model space the image shows (case-insensitive)' -r -f -a "extents\t'Always fit the drawing extents'
current\t'The current view, as last set by zoom, pan or view.set (a freshly opened drawing\'s view is its extents plus a 10% margin)'"
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -l config-dir -d 'The settings folder; plotter configurations are in its `plotters` folder (default: the platform\'s settings folder). An empty value means no settings folder' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -l fontalt -d 'The font that replaces a missing one (FONTALT)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -l fontfallback -d 'The fonts tried, in order, for characters a font lacks, comma-separated (FONTFALLBACK)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -l in-place -d 'Allow an output that is an input file, replacing the original'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand convert" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l script -d 'Command-line script text to run (`\\n` separates lines)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l script-file -d 'A script file (.scr) to run' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l cmd -d 'An engine command and its JSON parameters (default {}); see "--cmd chaining" in --help' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l save -d 'Save the drawing to this file; its extension picks the format (dxf, dwg, dwt, svg, png, pdf)' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l export -d 'Export the drawing to this file; its extension picks the format (dxf, dwg, dwt, svg, png, pdf)' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l window -d 'Show this rectangle (drawing units, x0<x1, y0<y1), centred and scaled to fit the image without distortion. A negative x0 needs the `=` form: --window=-10,0,10,5' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l view -d 'What part of model space the image shows (case-insensitive)' -r -f -a "extents\t'Always fit the drawing extents'
current\t'The current view, as last set by zoom, pan or view.set (a freshly opened drawing\'s view is its extents plus a 10% margin)'"
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l config-dir -d 'The settings folder; plotter configurations are in its `plotters` folder (default: the platform\'s settings folder). An empty value means no settings folder' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l fontalt -d 'The font that replaces a missing one (FONTALT)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l fontfallback -d 'The fonts tried, in order, for characters a font lacks, comma-separated (FONTFALLBACK)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l sample -d 'Open the built-in sample drawing'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l metric -d 'Start a new metric drawing'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -l in-place -d 'Allow an output that is an input file, replacing the original'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand run" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand commands" -l compact -d 'One line of JSON instead of pretty-printed'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand commands" -s h -l help -d 'Print help'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -l connect -d 'Bridge to the app\'s control channel (its --control port, e.g. 127.0.0.1:7979)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -l config-dir -d 'The settings folder; plotter configurations are in its `plotters` folder (default: the platform\'s settings folder). An empty value means no settings folder' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -l fontalt -d 'The font that replaces a missing one (FONTALT)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -l fontfallback -d 'The fonts tried, in order, for characters a font lacks, comma-separated (FONTFALLBACK)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -l lazy -d 'Reach the app at the first call instead of at startup, so the server can start before the app is open'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -l launch -d 'Like --lazy, and a call that finds nothing at HOST:PORT opens the app with that control port first (macOS)'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand mcp" -s h -l help -d 'Print help'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand perf" -s h -l help -d 'Print help'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand sample" -l config-dir -d 'The settings folder; plotter configurations are in its `plotters` folder (default: the platform\'s settings folder). An empty value means no settings folder' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand sample" -l fontalt -d 'The font that replaces a missing one (FONTALT)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand sample" -l fontfallback -d 'The fonts tried, in order, for characters a font lacks, comma-separated (FONTFALLBACK)' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand sample" -s h -l help -d 'Print help'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand roundtrip" -l out -d 'Where the report goes (default: `report` beside the files)' -r -F
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand roundtrip" -l tolerance -d 'How far numbers may move and still count as equal' -r
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand roundtrip" -l keep-saved -d 'Keep the saved files, in `saved` under the report folder'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand roundtrip" -l same-format -d 'Save only in each file\'s own format'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand roundtrip" -l no-census -d 'Don\'t count what each file holds (faster; no "read lost" column)'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand roundtrip" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "info" -d 'Print a drawing\'s summary as JSON'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "convert" -d 'Convert a drawing; OUT\'s extension picks the format (dxf, dwg, dwt, svg, png, pdf)'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "run" -d 'Open drawings (or start a new one), run scripts and commands in order, save or export the result'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "commands" -d 'Print the command catalog as JSON'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "mcp" -d 'Run the MCP server on stdio: a headless drawing session, or a bridge to the running app'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "perf" -d 'Time the engine on a synthetic N-entity drawing (default 200000), or the canvas display-list build of a drawing, zoomed in step by step'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "sample" -d 'Write a built-in sample drawing'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "roundtrip" -d 'Open each DXF/DWG, save it as DXF and DWG, reopen and compare; writes report.md and report.json'
complete -c cadcraft-cli -n "__fish_cadcraft_cli_using_subcommand help; and not __fish_seen_subcommand_from info convert run commands mcp perf sample roundtrip help" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
