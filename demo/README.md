# Demo Assets

VHS tape file for generating demo GIFs locally.

## Generate

```bash
# Requires: vhs, ttyd, ffmpeg, gifsicle
brew install vhs gifsicle

# Generate the demo GIF
vhs demo/ultrawork-demo.tape

# Compress if needed (GitHub has 10MB limit)
gifsicle -O3 --lossy=80 --colors 128 demo/ultrawork-demo.gif -o demo/ultrawork-demo.gif
```

## Notes

- Requires Claude Code and oh-my-claude plugin installed
- Uses `IS_DEMO=1` to minimize Claude's welcome banner
- Records 10 minutes at 10x playback speed (~60s GIF)
- GIF not committed to repo (large file, regenerate locally)
