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
    border-radius:15px;
}

QPushButton{
    background:qlineargradient(
        x1:0,y1:0,
        x2:1,y2:0,
        stop:0 #0066FF,
        stop:1 #00E5FF
    );

    color:white;

    font-weight:bold;

    border:none;

    border-radius:12px;

    padding:12px;
}

QPushButton:hover{
    background:#00E5FF;
}

QPushButton:pressed{
    background:#0050c8;
}

QTableWidget{

    background:#111827;

    border:none;

    border-radius:12px;

    gridline-color:#1F2937;
}

QHeaderView::section{

    background:#1F2937;

    border:none;

    padding:8px;

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