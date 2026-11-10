# Print an optspec for argparse to handle cmd's options that are independent of any subcommand.
function __fish_photocraft_cli_global_optspecs
    string join \n h/help V/version
end

function __fish_photocraft_cli_needs_command
    # Figure out if the current invocation already has a command.
    set -l cmd (commandline -opc)
    set -e cmd[1]
    argparse -s (__fish_photocraft_cli_global_optspecs) -- $cmd 2>/dev/null
    or return
    if set -q argv[1]
        # Also print the command, so this can be used to figure out what it is.
        echo $argv[1]
        return 1
    end
    return 0
end

function __fish_photocraft_cli_using_subcommand
    set -l cmd (__fish_photocraft_cli_needs_command)
    test -z "$cmd"
    and return 1
    contains -- $cmd[1] $argv
end

complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -s h -l help -d 'Print help'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -s V -l version -d 'Print version'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "convert" -d 'Convert between formats (.pcraft, .psd, .png, .jpg, .tif, .webp, .exr, …)'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "info" -d 'Print the document as JSON (size, mode, depth, layer tree)'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "run" -d 'Open a file (or start a new document), run engine commands in order, save the result'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "batch" -d 'Apply an action list to every image in a directory'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "droplet" -d 'Run a droplet (File › Automate › Create Droplet) on images and folders'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "commands" -d 'List the engine command registry'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "mcp" -d 'Run the MCP server on stdio (headless engine, or bridge to a running `photocraft --control <port>`)'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "serve" -d 'Keep one headless session open and answer JSON lines on stdio, or on 127.0.0.1:<PORT>'
complete -c photocraft-cli -n "__fish_photocraft_cli_needs_command" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l format -d 'Output format, overriding the output\'s extension (png, jpg, tif, webp, …)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l quality -d 'JPEG or WebP quality, 1-100. A WebP written with a quality is lossy, without one lossless' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l tiff-compression -d 'Compress TIFF output: none (the default), lzw or zip' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l tiff-transparency -d 'TIFF Save Transparency: on keeps the transparency (ahead of any alpha or spot channels), off composites the image over white. Without it: kept unless the document has alpha or spot channels' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l tga-bits -d 'A TGA\'s bits per pixel: 32 writes the alpha channel (or else the transparency) as its alpha, 24 none. Without it: 32 with an alpha channel or transparency, else 24' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l dpx-bits -d 'A DPX\'s bits per sample. Without it: 8 for an 8-bit document, else 16' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l dds-compression -d 'A DDS texture\'s compression: none (uncompressed, the default), bc1 (DXT1: alpha on or off), bc2 (DXT3) or bc3 (DXT5)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l jpeg-format -d 'A JPEG\'s scans, as JPEG Options picks them: baseline (the default), optimized (Huffman tables fitted to the image; RGB is written 4:2:0 and keeps the standard tables, so only Gray and CMYK shrink) or progressive' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l in-place -d 'Allow an <OUT> that is the <IN> file, replacing the original'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l approve-high-memory -d 'Explicitly approve high-memory PSD/PSB imports within the hard memory budget'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l gpu -d 'Prefer GPU rendering, falling back to CPU when unavailable or unsupported'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l no-gpu -d 'Use CPU rendering, overriding PHOTOCRAFT_GPU'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l tiff-layers -d 'Keep the layers in TIFF output (Photoshop layer data); TIFF output is flat without it'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l tiff-pyramid -d 'Also write a TIFF image pyramid: half-size copies after the full image'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l dds-mipmaps -d 'Also write a DDS texture\'s full mip chain'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -l pcraft-full-composite -d 'Request the flattened document at its canvas size in .pcraft output as composite/full.png; it may be omitted. Check the manifest\'s full_composite member'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand convert" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand info" -l compact -d 'One line of JSON instead of pretty-printed'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand info" -l approve-high-memory -d 'Explicitly approve high-memory PSD/PSB imports within the hard memory budget'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand info" -l detail -d 'Also list every text run and paragraph run, anti-aliasing and full layer-effect settings'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand info" -s h -l help -d 'Print help'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l new -d 'Start from a new document with these JSON parameters instead of opening a file' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l cmd -d 'An engine command to run; repeat for several, run in order' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l params -d 'JSON parameters for the --cmd before it (default {})' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l out -d 'Save the result to this file' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l format -d 'Output format, overriding the output\'s extension (png, jpg, tif, webp, …)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l quality -d 'JPEG or WebP quality, 1-100. A WebP written with a quality is lossy, without one lossless' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l tiff-compression -d 'Compress TIFF output: none (the default), lzw or zip' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l tiff-transparency -d 'TIFF Save Transparency: on keeps the transparency (ahead of any alpha or spot channels), off composites the image over white. Without it: kept unless the document has alpha or spot channels' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l tga-bits -d 'A TGA\'s bits per pixel: 32 writes the alpha channel (or else the transparency) as its alpha, 24 none. Without it: 32 with an alpha channel or transparency, else 24' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l dpx-bits -d 'A DPX\'s bits per sample. Without it: 8 for an 8-bit document, else 16' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l dds-compression -d 'A DDS texture\'s compression: none (uncompressed, the default), bc1 (DXT1: alpha on or off), bc2 (DXT3) or bc3 (DXT5)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l jpeg-format -d 'A JPEG\'s scans, as JPEG Options picks them: baseline (the default), optimized (Huffman tables fitted to the image; RGB is written 4:2:0 and keeps the standard tables, so only Gray and CMYK shrink) or progressive' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l in-place -d 'Allow an --out that is the <FILE>, replacing the original'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l approve-high-memory -d 'Explicitly approve high-memory PSD/PSB imports within the hard memory budget'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l gpu -d 'Prefer GPU rendering, falling back to CPU when unavailable or unsupported'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l no-gpu -d 'Use CPU rendering, overriding PHOTOCRAFT_GPU'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l tiff-layers -d 'Keep the layers in TIFF output (Photoshop layer data); TIFF output is flat without it'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l tiff-pyramid -d 'Also write a TIFF image pyramid: half-size copies after the full image'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l dds-mipmaps -d 'Also write a DDS texture\'s full mip chain'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -l pcraft-full-composite -d 'Request the flattened document at its canvas size in .pcraft output as composite/full.png; it may be omitted. Check the manifest\'s full_composite member'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand run" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l actions -d 'The action list: actions.json, a droplet, or a Photoshop Actions file (.atn)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l action -d 'Which action of an Actions set to play' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l in -d 'The folder of images to process' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l out -d 'The folder to write the results to, as <stem>.<ext>' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l naming -d 'Name each result with Batch tokens such as {name}, {serial}, {date}, and {ext}' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l start-serial -d 'First serial number used by --naming' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l error-log -d 'Write failed inputs and reasons to this text file' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l format -d 'Output format, overriding the output\'s extension (png, jpg, tif, webp, …)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l quality -d 'JPEG or WebP quality, 1-100. A WebP written with a quality is lossy, without one lossless' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l tiff-compression -d 'Compress TIFF output: none (the default), lzw or zip' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l tiff-transparency -d 'TIFF Save Transparency: on keeps the transparency (ahead of any alpha or spot channels), off composites the image over white. Without it: kept unless the document has alpha or spot channels' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l tga-bits -d 'A TGA\'s bits per pixel: 32 writes the alpha channel (or else the transparency) as its alpha, 24 none. Without it: 32 with an alpha channel or transparency, else 24' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l dpx-bits -d 'A DPX\'s bits per sample. Without it: 8 for an 8-bit document, else 16' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l dds-compression -d 'A DDS texture\'s compression: none (uncompressed, the default), bc1 (DXT1: alpha on or off), bc2 (DXT3) or bc3 (DXT5)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l jpeg-format -d 'A JPEG\'s scans, as JPEG Options picks them: baseline (the default), optimized (Huffman tables fitted to the image; RGB is written 4:2:0 and keeps the standard tables, so only Gray and CMYK shrink) or progressive' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l in-place -d 'An --out folder that is the --in folder is refused, as the results would replace the originals; --in-place allows it'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l recursive -d 'Include images in subfolders; every result goes straight into --out, so a later file of the same name replaces an earlier one'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l stop-on-error -d 'Stop after the first failed input'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l approve-high-memory -d 'Explicitly approve high-memory PSD/PSB imports within the hard memory budget'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l gpu -d 'Prefer GPU rendering, falling back to CPU when unavailable or unsupported'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l no-gpu -d 'Use CPU rendering, overriding PHOTOCRAFT_GPU'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l tiff-layers -d 'Keep the layers in TIFF output (Photoshop layer data); TIFF output is flat without it'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l tiff-pyramid -d 'Also write a TIFF image pyramid: half-size copies after the full image'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l dds-mipmaps -d 'Also write a DDS texture\'s full mip chain'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -l pcraft-full-composite -d 'Request the flattened document at its canvas size in .pcraft output as composite/full.png; it may be omitted. Check the manifest\'s full_composite member'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand batch" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand droplet" -l out -d 'The folder to write the results to' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand droplet" -s h -l help -d 'Print help'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand commands" -l filter -d 'Only the commands matching this text' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand commands" -l json -d 'Print the entries as JSON'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand commands" -s h -l help -d 'Print help'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l bridge -d 'Bridge to the PhotoCraft app listening here instead of a headless engine; a bare port means 127.0.0.1:<PORT>' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l control-token -d 'The control token (64 hex digits)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l control-token-file -d 'A file holding the control token, used instead of --control-token (a server creates it when missing)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l automation-read-root -d 'The folder automation may read from (none without it)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l automation-write-root -d 'The folder automation may write to (none without it)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l gpu -d 'Prefer GPU rendering, falling back to CPU when unavailable or unsupported'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -l no-gpu -d 'Use CPU rendering, overriding PHOTOCRAFT_GPU'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand mcp" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l port -d 'Listen on 127.0.0.1:<PORT> instead of stdio' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l control-token -d 'The control token (64 hex digits)' -r
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l control-token-file -d 'A file holding the control token, used instead of --control-token (a server creates it when missing)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l automation-read-root -d 'The folder automation may read from (none without it)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l automation-write-root -d 'The folder automation may write to (none without it)' -r -F
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l gpu -d 'Prefer GPU rendering, falling back to CPU when unavailable or unsupported'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -l no-gpu -d 'Use CPU rendering, overriding PHOTOCRAFT_GPU'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand serve" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "convert" -d 'Convert between formats (.pcraft, .psd, .png, .jpg, .tif, .webp, .exr, …)'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "info" -d 'Print the document as JSON (size, mode, depth, layer tree)'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "run" -d 'Open a file (or start a new document), run engine commands in order, save the result'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "batch" -d 'Apply an action list to every image in a directory'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "droplet" -d 'Run a droplet (File › Automate › Create Droplet) on images and folders'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "commands" -d 'List the engine command registry'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "mcp" -d 'Run the MCP server on stdio (headless engine, or bridge to a running `photocraft --control <port>`)'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "serve" -d 'Keep one headless session open and answer JSON lines on stdio, or on 127.0.0.1:<PORT>'
complete -c photocraft-cli -n "__fish_photocraft_cli_using_subcommand help; and not __fish_seen_subcommand_from convert info run batch droplet commands mcp serve help" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
