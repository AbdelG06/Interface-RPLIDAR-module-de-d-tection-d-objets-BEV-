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
    border:1px solid #223047;
    border-radius:12px;
}

QScrollArea{
    border:none;
    background:transparent;
}

QSplitter::handle{
    background:#0B0F15;
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
    font-weight:700;
    border:1px solid #243047;
    border-radius:10px;
    padding:9px 13px;
}

QPushButton:hover{
    background:#172033;
    border:1px solid #00E5FF;
    color:#FFFFFF;
}

QPushButton:pressed{
    background:#0F172A;
}

QPushButton:disabled{
    background:#1E293B;
    border:1px solid #273449;
    color:#64748B;
}

QTableWidget{
    background:#0F172A;
    border:1px solid #223047;
    border-radius:12px;
    gridline-color:#1F2937;
    selection-background-color:#11334A;
}

QHeaderView::section{
    background:#111827;
    border:none;
    border-bottom:1px solid #223047;
    padding:9px;
    font-weight:700;
    color:#E5E7EB;
}

QListWidget{
    outline:none;
}

QLabel#Title{
    font-size:22pt;
    font-weight:800;
    color:#00E5FF;
}

QLabel#Status{
    font-size:10pt;
    color:#00FF95;
    font-weight:700;
}

"""