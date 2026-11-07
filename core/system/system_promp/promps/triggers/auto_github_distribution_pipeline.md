# 📦 PASSIVE TRIGGER: GITHUB DISTRIBUTION & ISO REPRODUCTION PROTOCOL
* **Detected Context**: GitHub repository push or ISO distribution staging (upload-flowork-os.sh, build-iso.sh, flowork-os).
* **Operational Invariants**:
  1. Strict Zero-Leak: Never stage .env, personal tokens (Downloads/token), SSH keys (~/.ssh), browser profiles (~/.config/google-chrome, /var/lib/lightdm/.config), or agent chat transcripts (history/chats/).
  2. GitHub File Size Barrier (<100MB): Reject files >95MB. Omit massive kernel build objects (linux-rust/ 3.5GB and initrd 113MB); package kernel as compact .deb binaries.
  3. Skeleton Desktop Parity: Mirror /etc/skel/ to guarantee identical 1:1 user desktop UI upon live boot.
  4. Credential Sanitation: Immediately restore remote URL to clean HTTPS post-push without embedding authentication tokens.
  5. Autologin & User DB: Enforce pure 'flowork:1000:1000' user; purge host accounts from user databases and lock LightDM to autologin-user=flowork.
