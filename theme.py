DARK_THEME = """

QMainWindow{
    background:#0B0F15;
}

QWidget{
    background:#0B0F15;
    color:#E5E7EB;
    font-family:'Segoe UI';
    font-size:10pt;
}

QFrame#Card{
    background:#111827;
    border:1px solid #1F2937;
    border-radius:16px;
}

QScrollArea{
    border:none;
    background:transparent;
}

QScrollBar:vertical{
    background:transparent;
    width:10px;
    margin:12px 2px 12px 2px;
}

QScrollBar::handle:vertical{
    background:#334155;
    border-radius:5px;
    min-height:26px;
}

QScrollBar::handle:vertical:hover{
    background:#475569;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical{
    height:0px;
    background:transparent;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical{
    background:transparent;
}

QPushButton{
    background:#111827;
    color:#E5E7EB;
    font-weight:600;
    border:1px solid #243047;
    border-radius:12px;
    padding:10px 14px;
}

QPushButton:hover{
    background:#172033;
    border:1px solid #00E5FF;
}

QPushButton:pressed{
    background:#0F172A;
}

QTableWidget{

    background:#111827;

    border:none;

    border-radius:12px;

    gridline-color:#1F2937;
}

QHeaderView::section{

    background:#182033;

    border:none;

    padding:10px;

    font-weight:bold;

    color:white;
}

QLabel#Title{

    font-size:22pt;

    font-weight:700;

    color:#00E5FF;
}

QLabel#Status{

    font-size:11pt;

    color:#00FF95;

    font-weight:bold;
}

"""