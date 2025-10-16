# TalkTuah Styles

Modular TCSS (Textual CSS) files for the TalkTuah TUI application.

## Structure

```
styles/
├── README.md          # This file
├── main.tcss          # Main application layout
├── chat.tcss          # Chat and messaging components
├── footer.tcss        # Footer and keybindings
└── settings.tcss      # Settings modal and related widgets
```

## File Organization

### `main.tcss` - Main Application Layout
- Screen and Header styles
- Main container layout
- Conversation box structure
- Borders and side panels

### `chat.tcss` - Chat Components
- Message scroll container
- ChatMessage widget
- Chat input field
- System messages

### `footer.tcss` - Footer Components
- CustomFooter layout
- Keybinding buttons
- Footer borders and spacers

### `settings.tcss` - Settings Modal
- Settings modal container
- Theme options
- Model manager
- Model download interface
- Endpoint configuration
- All settings-related widgets

## Usage

### In Python Files

```python
from textual.app import App

class TuivLLM(App):
    # Single file
    CSS_PATH = "styles/main.tcss"
    
    # Multiple files (loaded in order)
    CSS_PATH = [
        "styles/main.tcss",
        "styles/chat.tcss",
        "styles/footer.tcss",
    ]
```

### Textual CSS Features

TCSS supports:
- **Selectors**: `#id`, `.class`, `Widget`
- **Pseudo-classes**: `:focus`, `:hover`
- **Variables**: `$primary`, `$background`
- **Layout**: `dock`, `layout`, `align`
- **Spacing**: `padding`, `margin`, `width`, `height`
- **Colors**: `color`, `background`, `border`

## Best Practices

1. **Keep styles modular** - One file per major component
2. **Use descriptive IDs** - `#chat-input` not `#input1`
3. **Leverage variables** - Use `$primary` instead of hardcoded colors
4. **Comment sections** - Explain complex layouts
5. **Avoid duplication** - Share styles across related widgets

## Editing Styles

1. Edit the appropriate `.tcss` file
2. Save changes
3. Restart the TUI to see updates

**Note:** Unlike web CSS, Textual doesn't support hot-reloading of styles. You must restart the application after changes.

## Textual Documentation

For more information on TCSS:
- [Textual CSS Guide](https://textual.textualize.io/guide/CSS/)
- [CSS Styles Reference](https://textual.textualize.io/styles/)
