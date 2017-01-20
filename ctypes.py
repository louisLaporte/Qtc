from enum import Enum

class MouseButton(Enum):
    LeftButton   = 0x0000001F
    MiddleButton = 0x000007C0
    RightButton  = 0x0001F000
    Wheel        = 0x007C0000

class MouseAction(Enum):
    Released      = 0x01
    Pressed       = 0x02
    Clicked       = 0x04
    DoubleClicked = 0x08
    TripleClicked = 0x10

class CheckState(Enum):
    Unchecked        = 0
    PartiallyChecked = 1
    Checked          = 2
class Corner(Enum):
    TopLeftCorner     = 0x0
    TopRightCorner    = 0x1
    BottomLeftCorner  = 0x2
    BottomRightCorner = 0x3

class Edge(Enum):
    TopEdge     = 0x1
    LeftEdge    = 0x2
    RightEdge   = 0x4
    BottomEdge  = 0x8

class FindChildOption(Enum):
    FindDirectChildrenOnly  = 0x0
    FindChildrenRecursively = 0x1

class FocusPolicy(Enum):
    NoFocus     = 0x00
    TabFocus    = 0x01
    ClickFocus  = 0x02
    StrongFocus = TabFocus | ClickFocus | 0x08
    WheelFocus  = StrongFocus | 0x04

class FocusReason(Enum):
    Mouse        = 0
    Tab          = 1
    Backtab      = 2
    ActiveWindow = 3
    Popup        = 4
    Shortcut     = 5
    MenuBar      = 6
    Other        = 7

class WindowType(Enum):
    Widget  = 0x00
    Window  = 0x01
    Dialog  = 0x02 | Window
    Desktop = 0x10 | Window

class ItemFlag(Enum):
    NoFlags          = 0x000
    IsSelectable     = 0x001
    IsEditable       = 0x002
    IsUserCheckable  = 0x010
    IsEnabled        = 0x020
    IsAutoTristate   = 0x040
    NeverHasChildren = 0x080
    IsUserTristate   = 0x100

class Key(Enum):
    Escape     = 0x01b
    Tab        = 0x009
    Backtab    = 0x161
    Backspace  = 0x107
    Enter      = 0x00a
    Insert     = 0x14b
    Delete     = 0x14a
    Down       = 0x102
    Up         = 0x103
    Left       = 0x104
    Right      = 0x105
    F1         = 0x109
    F2         = 0x10a
    F3         = 0x10b
    F4         = 0x10c
    F5         = 0x10d
    F6         = 0x10e
    F7         = 0x10f
    F8         = 0x110
    F9         = 0x111
    F10        = 0x112
    F11        = 0x113
    F12        = 0x114
    Space      = 0x20
    Any        = Space
    Exclam     = 0x21
    QuoteDbl   = 0x22
    NumberSign = 0x23
    Dollar     = 0x24
    Percent    = 0x25
    Ampersand  = 0x26
    Apostrophe = 0x27
    ParenLeft  = 0x28
    ParenRight = 0x29
    Asterisk   = 0x2a
    Plus       = 0x2b
    Comma      = 0x2c
    Minus      = 0x2d
    Period     = 0x2e
    Slash      = 0x2f
    Zero       = 0x30 # 0
    One        = 0x31 # 1
    Two        = 0x32 # 2
    Three      = 0x33 # 3
    Four       = 0x34 # 4
    Five       = 0x35 # 5
    Six        = 0x36 # 6
    Seven      = 0x37 # 7
    Eight      = 0x38 # 8
    Nine       = 0x39 # 9
    Colon      = 0x3a
    Semicolon  = 0x3b
    Less       = 0x3c
    Equal      = 0x3d
    Greater    = 0x3e
    Question   = 0x3f
    At         = 0x40
    A          = 0x41
    B          = 0x42
    C          = 0x43
    D          = 0x44
    E          = 0x45
    F          = 0x46
    G          = 0x47
    H          = 0x48
    I          = 0x49
    J          = 0x4a
    K          = 0x4b
    L          = 0x4c
    M          = 0x4d
    N          = 0x4e
    O          = 0x4f
    P          = 0x50
    Q          = 0x51
    R          = 0x52
    S          = 0x53
    T          = 0x54
    U          = 0x55
    V          = 0x56
    W          = 0x57
    X          = 0x58
    Y          = 0x59
    Z          = 0x5a
#    key_list = [ "KEY_MIN",
#                "KEY_BREAK",
#                "KEY_DOWN", "KEY_UP", "KEY_LEFT", "KEY_RIGHT",
#                "KEY_HOME",
#                "KEY_BACKSPACE",
#
#                "KEY_F0", "KEY_F1", "KEY_F2", "KEY_F3", "KEY_F4", "KEY_F5",
#                "KEY_F6", "KEY_F7", "KEY_F8", "KEY_F9", "KEY_F10", "KEY_F11",
#                "KEY_F12", "KEY_F13", "KEY_F14", "KEY_F15", "KEY_F16", "KEY_F17",
#                "KEY_F18", "KEY_F19", "KEY_F20", "KEY_F21", "KEY_F22", "KEY_F23",
#                "KEY_F24", "KEY_F25", "KEY_F26", "KEY_F27", "KEY_F28", "KEY_F29",
#                "KEY_F30", "KEY_F31", "KEY_F32", "KEY_F33", "KEY_F34", "KEY_F35",
#                "KEY_F36", "KEY_F37", "KEY_F38", "KEY_F39", "KEY_F40", "KEY_F41",
#                "KEY_F42", "KEY_F43", "KEY_F44", "KEY_F45", "KEY_F46", "KEY_F47",
#                "KEY_F48", "KEY_F49", "KEY_F50", "KEY_F51", "KEY_F52", "KEY_F53",
#                "KEY_F54", "KEY_F55", "KEY_F56", "KEY_F57", "KEY_F58", "KEY_F59",
#                "KEY_F60", "KEY_F61", "KEY_F62", "KEY_F63", "KEY_F64",
#
#                "KEY_DL", "KEY_IL", "KEY_DC", "KEY_IC", "KEY_EIC",
#                "KEY_CLEAR", "KEY_EOS", "KEY_EOL",
#                "KEY_SF", "KEY_SR",
#                "KEY_NPAGE", "KEY_PPAGE",
#                "KEY_STAB", "KEY_CTAB", "KEY_CATAB",
#                "KEY_ENTER",
#                "KEY_SRESET",
#                "KEY_RESET",
#                "KEY_PRINT",
#                "KEY_LL",
#                "KEY_A1",
#                "KEY_A3",
#                "KEY_B2",
#                "KEY_C1",
#                "KEY_C3",
#                "KEY_BTAB",
#                "KEY_BEG",
#                "KEY_CANCEL",
#                "KEY_CLOSE",
#                "KEY_COMMAND",
#                "KEY_COPY",
#                "KEY_CREATE",
#                "KEY_END",
#                "KEY_EXIT",
#                "KEY_FIND",
#                "KEY_HELP",
#                "KEY_MARK",
#                "KEY_MESSAGE",
#                "KEY_MOVE",
#                "KEY_NEXT",
#                "KEY_OPEN",
#                "KEY_OPTIONS",
#                "KEY_PREVIOUS",
#                "KEY_REDO",
#                "KEY_REFERENCE",
#                "KEY_REFRESH",
#                "KEY_REPLACE",
#                "KEY_RESTART",
#                "KEY_RESUME",
#                "KEY_SAVE",
#                "KEY_SBEG",
#                "KEY_SCANCEL", "KEY_SCOMMAND", "KEY_SCOPY", "KEY_SCREATE",
#                "KEY_SDC", "KEY_SDL", "KEY_SELECT", "KEY_SEND", "KEY_SEOL",
#                "KEY_SEXIT", "KEY_SFIND", "KEY_SHELP", "KEY_SHOME", "KEY_SIC",
#                "KEY_SLEF", "KEY_SMESSAGE", "KEY_SMOVE", "KEY_SNEXT", "KEY_SOPTIONS",
#                "KEY_SPREVIOUS", "KEY_SPRINT", "KEY_SREDO", "KEY_SREPLACE",
#                "KEY_SRIGHT", "KEY_SRSUME", "KEY_SSAVE", "KEY_SSUSPEND",
#                "KEY_SUNDO", "KEY_SUSPEND",
#                "KEY_UNDO",
#                "KEY_MOUSE",
#                "KEY_RESIZE",
#                "KEY_MAX",
#
#                "KEY_IC",
#                "KEY_DC",
#                "KEY_HOME",
#                "KEY_END",
#                "KEY_NPAGE",
#                "KEY_PPAGE"]
