use clap::{Args, Parser, Subcommand, ValueEnum};
use std::path::PathBuf;

#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum OutputFormatArg {
    Text,
    Json,
    #[value(name = "stream-json")]
    StreamJson,
}

#[derive(Debug, Parser)]
#[command(
    name = "mrflow",
    version = "2.0.0-sovereign",
    about = "Mr. Flow Sovereign Agent - Defaults to interactive mode. Use -p/--prompt for non-interactive (headless) mode.",
    long_about = "Mr. Flow Sovereign Agent (Clean-Room Native Rust Engine) - Flowork OS.\nDefaults to interactive Glass HUD mode. Use -p/--prompt for headless and stream-json automation."
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Option<Commands>,

    /// Initial prompt. Runs in interactive mode by default; use -p/--prompt for non-interactive.
    #[arg(value_name = "query")]
    pub query: Vec<String>,

    /// Run in debug mode (open debug logs)
    #[arg(short = 'd', long = "debug", default_value_t = false)]
    pub debug: bool,

    /// Model identifier (e.g. gemini-3.8-flash-high, deepseek-v4-9b-uncensored)
    #[arg(short = 'm', long = "model")]
    pub model: Option<String>,

    /// Run in non-interactive (headless) mode with the given prompt. Appended to stdin if any.
    #[arg(short = 'p', long = "prompt")]
    pub prompt: Option<String>,

    /// Execute the provided prompt and continue in interactive mode
    #[arg(short = 'i', long = "prompt-interactive")]
    pub prompt_interactive: Option<String>,

    /// Trust the current workspace for this session
    #[arg(long = "skip-trust", default_value_t = false)]
    pub skip_trust: bool,

    /// Start Mr. Flow in a git worktree
    #[arg(short = 'w', long = "worktree")]
    pub worktree: Option<Option<String>>,

    /// Run in sandbox mode
    #[arg(short = 's', long = "sandbox", default_value_t = false)]
    pub sandbox: bool,

    /// Automatically accept all actions autonomously (Sovereign mode)
    #[arg(long = "sovereign", default_value_t = false)]
    pub sovereign: bool,

    /// Set the approval mode: default, auto_edit, sovereign, yolo, plan
    #[arg(long = "approval-mode")]
    pub approval_mode: Option<String>,

    /// Additional policy files or directories to load
    #[arg(long = "policy", value_delimiter = ',')]
    pub policy: Vec<PathBuf>,

    /// Additional admin policy files or directories to load
    #[arg(long = "admin-policy", value_delimiter = ',')]
    pub admin_policy: Vec<PathBuf>,

    /// Starts the agent in ACP (stdio JSON-RPC) mode
    #[arg(long = "acp", default_value_t = false)]
    pub acp: bool,

    /// Starts the agent in ACP mode (deprecated alias)
    #[arg(long = "experimental-acp", default_value_t = false)]
    pub experimental_acp: bool,

    /// Allowed MCP server names
    #[arg(long = "allowed-mcp-server-names", value_delimiter = ',')]
    pub allowed_mcp_server_names: Option<Vec<String>>,

    /// Tools allowed without confirmation
    #[arg(long = "allowed-tools", value_delimiter = ',')]
    pub allowed_tools: Vec<String>,

    /// Extensions to enable
    #[arg(short = 'e', long = "extensions", value_delimiter = ',')]
    pub extensions: Vec<String>,

    /// List all available extensions and exit
    #[arg(short = 'l', long = "list-extensions", default_value_t = false)]
    pub list_extensions: bool,

    /// Resume a previous session ("latest", index number, or UUID)
    #[arg(short = 'r', long = "resume")]
    pub resume: Option<String>,

    /// Load a session from a JSON/JSONL file
    #[arg(long = "session-file")]
    pub session_file: Option<PathBuf>,

    /// Start a new session with a manually provided UUID
    #[arg(long = "session-id")]
    pub session_id: Option<String>,

    /// List available sessions for the current project and exit
    #[arg(long = "list-sessions", default_value_t = false)]
    pub list_sessions: bool,

    /// Delete a session by index number or session ID
    #[arg(long = "delete-session")]
    pub delete_session: Option<String>,

    /// Additional directories to include in the workspace
    #[arg(long = "include-directories", value_delimiter = ',')]
    pub include_directories: Vec<PathBuf>,

    /// Enable screen reader mode for accessibility
    #[arg(long = "screen-reader", default_value_t = false)]
    pub screen_reader: bool,

    /// Output format for non-interactive CLI
    #[arg(short = 'o', long = "output-format", value_enum)]
    pub output_format: Option<OutputFormatArg>,

    /// Disable sanitization of ANSI escape sequences in model output
    #[arg(long = "raw-output", default_value_t = false)]
    pub raw_output: bool,

    /// Suppress the security warning when using --raw-output
    #[arg(long = "accept-raw-output-risk", default_value_t = false)]
    pub accept_raw_output_risk: bool,
}

#[derive(Debug, Subcommand)]
pub enum Commands {
    /// Manage MCP servers
    Mcp(McpArgs),
    /// Manage agent skills
    #[command(alias = "skill")]
    Skills(SkillsArgs),
    /// Manage Mr. Flow extensions
    #[command(alias = "extension")]
    Extensions(ExtensionsArgs),
    /// Manage Mr. Flow hooks
    #[command(alias = "hook")]
    Hooks(HooksArgs),
    /// Manage local Gemma / SLM model routing
    Gemma(GemmaArgs),
}

#[derive(Debug, Args)]
pub struct McpArgs {
    #[command(subcommand)]
    pub action: McpAction,
}

#[derive(Debug, Subcommand)]
pub enum McpAction {
    /// Add an MCP server to user settings
    Add {
        name: String,
        command_or_url: String,
        args: Vec<String>,
    },
    /// Remove an MCP server from user settings
    Remove { name: String },
    /// List all configured MCP servers
    List,
    /// Enable an MCP server
    Enable { name: String },
    /// Disable an MCP server
    Disable { name: String },
}

#[derive(Debug, Args)]
pub struct SkillsArgs {
    #[command(subcommand)]
    pub action: SkillsAction,
}

#[derive(Debug, Subcommand)]
pub enum SkillsAction {
    /// List discovered agent skills
    List {
        #[arg(long = "all", default_value_t = false)]
        all: bool,
    },
    /// Enable an agent skill
    Enable { name: String },
    /// Disable an agent skill
    Disable {
        name: String,
        #[arg(long = "scope")]
        scope: Option<String>,
    },
    /// Install an agent skill from git URL or local path
    Install {
        source: String,
        #[arg(long = "scope")]
        scope: Option<String>,
        #[arg(long = "path")]
        path: Option<String>,
    },
    /// Link an agent skill from a local path
    Link { path: PathBuf },
    /// Uninstall an agent skill by name
    Uninstall {
        name: String,
        #[arg(long = "scope")]
        scope: Option<String>,
    },
}

#[derive(Debug, Args)]
pub struct ExtensionsArgs {
    #[command(subcommand)]
    pub action: ExtensionsAction,
}

#[derive(Debug, Subcommand)]
pub enum ExtensionsAction {
    List,
    Install {
        source: String,
        #[arg(long = "auto-update", default_value_t = false)]
        auto_update: bool,
        #[arg(long = "pre-release", default_value_t = false)]
        pre_release: bool,
    },
    Uninstall { names: Vec<String> },
    Update {
        name: Option<String>,
        #[arg(long = "all", default_value_t = false)]
        all: bool,
    },
    Disable {
        name: String,
        #[arg(long = "scope")]
        scope: Option<String>,
    },
    Enable {
        name: String,
        #[arg(long = "scope")]
        scope: Option<String>,
    },
    Link { path: PathBuf },
    New {
        path: PathBuf,
        template: Option<String>,
    },
    Validate { path: PathBuf },
    Config {
        name: Option<String>,
        setting: Option<String>,
    },
}

#[derive(Debug, Args)]
pub struct HooksArgs {
    #[command(subcommand)]
    pub action: HooksAction,
}

#[derive(Debug, Subcommand)]
pub enum HooksAction {
    /// Migrate hooks into ~/.flowork/hooks
    Migrate,
}

#[derive(Debug, Args)]
pub struct GemmaArgs {
    #[command(subcommand)]
    pub action: GemmaAction,
}

#[derive(Debug, Subcommand)]
pub enum GemmaAction {
    Setup,
    Start,
    Stop,
    Status,
    Logs,
}
