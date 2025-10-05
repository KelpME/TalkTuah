# TuivLLM Default Color Palette

Beautiful modern color scheme inspired by Tokyo Night and modern terminal themes.

## Color Palette

### Background & Text
- **Background**: `#1a1b26` - Deep dark blue-gray (comfortable for long sessions)
- **Foreground**: `#c0caf5` - Soft white (easy on the eyes)

### Message Colors
- **User Messages**: `#7aa2f7` - Bright cyan/blue (cool, calm)
- **AI Messages**: `#bb9af7` - Vibrant purple/magenta (creative, intelligent)
- **System Messages**: `#565f89` - Muted gray (subtle, non-intrusive)

### UI Elements
- **Borders**: `#7dcfff` - Accent cyan (modern, clean)
- **Input Border**: `#7dcfff` - Matching accent cyan

### Status Indicators
- **Connected**: `#9ece6a` - Green (healthy, active)
- **Processing**: `#e0af68` - Yellow/orange (working, in-progress)
- **Error**: `#f7768e` - Red/pink (attention needed)

### Scrollbars
- **Default**: `#7dcfff` - Cyan
- **Hover**: `#7aa2f7` - Blue
- **Active**: `#bb9af7` - Purple

### Timestamps
- **Timestamp**: `#565f89` - Subtle gray (informative but not distracting)

## Color Philosophy

This palette follows modern design principles:

1. **High Contrast** - Dark background with vibrant accents
2. **Eye Comfort** - Soft colors reduce eye strain
3. **Visual Hierarchy** - Different elements have distinct colors
4. **Semantic Colors** - Status colors match their meaning
5. **Cohesive** - All colors work together harmoniously

## Accessibility

- ✅ Sufficient contrast ratios for readability
- ✅ Distinct colors for different message types
- ✅ Status colors follow universal conventions
- ✅ Works well in both bright and dark environments

## Customization

To create your own theme based on this palette:

```bash
cp themes/terminal.theme ~/.config/tuivllm/themes/mytheme.theme
# Edit colors in mytheme.theme
echo 'color_theme = "mytheme"' > tuivllm.conf
```

## Preview

```
┌─────────────────────────────────────┐
│ Background: #1a1b26 (dark blue-gray)│
│                                     │
│ ┌─ User (#7aa2f7) ─────────────┐   │
│ │ Bright cyan/blue message     │   │
│ └──────────────────────────────┘   │
│                                     │
│ ┌─ AI (#bb9af7) ───────────────┐   │
│ │ Vibrant purple response      │   │
│ └──────────────────────────────┘   │
│                                     │
│ System: #565f89 (muted gray)        │
│                                     │
│ Border: #7dcfff (accent cyan)       │
└─────────────────────────────────────┘
```

## Inspiration

This color scheme draws inspiration from:
- Tokyo Night theme
- Modern terminal emulators
- Material Design color principles
- Accessibility guidelines

The result is a beautiful, functional theme that looks great and reduces eye strain during long coding/chat sessions.
