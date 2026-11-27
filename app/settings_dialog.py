"""Live appearance and sound controls for the desktop companion."""
from PySide6.QtCore import Qt,QSize,QTimer,QPointF,QRectF
import time
from pathlib import Path
from PySide6.QtGui import QIcon,QPixmap,QPainter,QColor,QPen,QLinearGradient,QPainterPath
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QTabWidget,QWidget,QLabel,QComboBox,QPushButton,QSlider,QCheckBox,QFileDialog,QMessageBox,QScrollArea,QFrame)
from preferences import SKINS,PACKS,import_skin
from i18n import translate
from version import VERSION
from custom_audio import SOUND_SLOTS,import_sound

PYTHENIANS_STYLE = '''
QDialog { background:#f5f0e6; }
QWidget { color:#30253c; font-family:"Segoe UI", "DejaVu Sans"; font-size:13px; }
QLabel { background:transparent; }
QLabel#brand { color:#f8eccb; font-family:"Georgia", "DejaVu Serif"; font-size:27px; font-weight:bold; }
QLabel#subtitle { color:#e1cda8; font-size:12px; }
QLabel#eyebrow { color:#d5ea9e; font-size:10px; font-weight:bold; }
QLabel#sectionTitle { color:#603174; font-size:14px; font-weight:bold; padding-top:8px; }
QLabel#sectionNote, QLabel#hint { color:#756b7b; font-size:12px; }
QLabel#value { color:#603174; background:#eee5f2; border:1px solid #d9c7df; border-radius:6px; padding:4px; font-weight:bold; }
QFrame#previewCard { background:#ede5d8; border:1px solid #cdb680; border-radius:12px; }
QLabel#previewTitle { color:#735b29; font-size:10px; font-weight:bold; }
QTabWidget::pane { background:#fffcf5; border:1px solid #d8c9a6; border-radius:10px; top:-1px; }
QTabBar::tab { background:#eae2d5; color:#6c5e71; border:1px solid #d8c9a6; padding:11px 16px; margin-right:5px; border-top-left-radius:8px; border-top-right-radius:8px; }
QTabBar::tab:selected { background:#603174; color:#fff1cf; border-color:#603174; }
QTabBar::tab:hover:!selected { background:#e5d7eb; color:#603174; }
QScrollArea, QWidget#tabPage { background:#fffcf5; border:0; }
QComboBox, QPushButton { background:#fffdf8; border:1px solid #ccbc9d; border-radius:7px; padding:8px 10px; min-height:19px; }
QComboBox:hover, QPushButton:hover { border-color:#996dad; background:#f2eaf5; }
QComboBox:focus, QPushButton:focus, QCheckBox:focus { border:2px solid #87569a; }
QComboBox::drop-down { width:24px; border:0; }
QComboBox QAbstractItemView { background:#fffcf5; color:#30253c; selection-background-color:#603174; selection-color:#fff1cf; outline:0; }
QPushButton:pressed { background:#e3d2eb; }
QPushButton#primary { color:#fff2d2; background:#603174; border:1px solid #b58b3c; padding:10px 18px; font-weight:bold; }
QPushButton#primary:hover { background:#75438a; border-color:#d8b65d; }
QSlider::groove:horizontal { height:6px; background:#e7dfd0; border-radius:3px; }
QSlider::sub-page:horizontal { background:#87529c; border-radius:3px; }
QSlider::handle:horizontal { width:16px; margin:-6px 0; background:#f0ce76; border:2px solid #8e6927; border-radius:9px; }
QSlider::handle:horizontal:hover { background:#ffe5a1; border-color:#603174; }
QSlider:focus { background:#f0e7f3; border-radius:5px; }
QCheckBox { spacing:10px; padding:7px 2px; }
QCheckBox::indicator { width:18px; height:18px; border:1px solid #ac9871; border-radius:5px; background:#fffdf8; }
QCheckBox::indicator:checked { background:#603174; border:3px solid #c6ab64; }
QCheckBox::indicator:hover { border-color:#87529c; }
QScrollBar:vertical { background:#f4eee3; width:10px; margin:4px 1px; border-radius:5px; }
QScrollBar::handle:vertical { background:#baa9c3; min-height:30px; border-radius:4px; }
QScrollBar::handle:vertical:hover { background:#87529c; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:transparent; }
QToolTip { color:#fff3d5; background:#43234f; border:1px solid #c5a35a; padding:6px; }
'''

class PytheniansBanner(QFrame):
    """Resolution-independent Greek key ornament; no external theme assets."""
    def __init__(self,parent=None):
        super().__init__(parent); self.setMinimumHeight(126)
        box=QVBoxLayout(self);box.setContentsMargins(24,14,90,32);box.setSpacing(3)
        for text,name in [('PIRB DESK  /  PYTHENIANS','eyebrow'),('Thánh điện của PIRB','brand'),('Tùy chỉnh không gian của bạn','subtitle')]:
            label=QLabel(text);label.setObjectName(name);box.addWidget(label)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient=QLinearGradient(0,0,self.width(),self.height());gradient.setColorAt(0,QColor('#382044'));gradient.setColorAt(1,QColor('#743d85'))
        p.setBrush(gradient);p.setPen(QPen(QColor('#b89750'),1));p.drawRoundedRect(QRectF(.5,.5,self.width()-1,self.height()-1),12,12)
        p.setPen(QPen(QColor('#c8a85f'),1.3))
        for x in range(22,self.width()-25,28):
            y=self.height()-18;path=QPainterPath(QPointF(x,y));path.lineTo(x+20,y);path.lineTo(x+20,y-10);path.lineTo(x+6,y-10);path.lineTo(x+6,y-4);path.lineTo(x+14,y-4);p.drawPath(path)
        # A gold staff and olive leaves echo the supplied character illustration.
        cx=self.width()-46;p.setPen(QPen(QColor('#e8c970'),2));p.drawLine(QPointF(cx,28),QPointF(cx,79))
        p.setBrush(QColor('#f2d68b'));path=QPainterPath(QPointF(cx,16));path.lineTo(cx-7,34);path.lineTo(cx,30);path.lineTo(cx+7,34);path.closeSubpath();p.drawPath(path)
        p.setPen(QPen(QColor('#abc76b'),2))
        for side in (-1,1):
            for i in range(3):
                p.save();p.translate(cx+side*(13+i*3),67-i*10);p.rotate(side*32);p.drawEllipse(QRectF(-3,-7,6,14));p.restore()

class SettingsDialog(QDialog):
    def __init__(self,owner):
        super().__init__(None);self.owner=owner;self.ready=False;self.controls={};self.value_labels={}
        self.setWindowTitle('Pirb Desk · Tùy chỉnh');self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(740,850);self.setMinimumWidth(660)
        self.setStyleSheet(PYTHENIANS_STYLE)
        layout=QVBoxLayout(self);layout.setContentsMargins(18,18,18,18);layout.setSpacing(13)
        layout.addWidget(PytheniansBanner(self))
        language_row=QHBoxLayout();language_row.addWidget(QLabel('Ngôn ngữ / Language'));language_row.addStretch()
        self.language=QComboBox();self.language.setAccessibleName('Ngôn ngữ / Language')
        self.language.addItem('Tiếng Việt','vi');self.language.addItem('English','en');self.language.setCurrentIndex(max(0,self.language.findData(owner.prefs.get('language','vi'))))
        language_row.addWidget(self.language);layout.addLayout(language_row)
        preview_card=QFrame();preview_card.setObjectName('previewCard');preview_layout=QVBoxLayout(preview_card);preview_layout.setContentsMargins(12,9,12,5);preview_layout.setSpacing(0)
        preview_title=QLabel('XEM TRƯỚC TRỰC TIẾP');preview_title.setObjectName('previewTitle');preview_layout.addWidget(preview_title)
        self.preview=QLabel();self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.preview.setFixedHeight(155);preview_layout.addWidget(self.preview);layout.addWidget(preview_card)
        tabs=QTabWidget();layout.addWidget(tabs)
        scene=QWidget();vf=QFormLayout(scene);self.add_scroll_tab(tabs,scene,'Vị trí & kích thước')
        self.section(vf,'Không gian của PIRB','Xoay, thu phóng và chọn vị trí trên màn hình.')
        self.slider(vf,'Chiều rộng cảnh','scene_width',180,1200,'px')
        self.slider(vf,'Xoay toàn cảnh','scene_rotation',-180,180,'°')
        quick=QWidget();qr=QHBoxLayout(quick);qr.setContentsMargins(0,0,0,0)
        for title,angle in [('Canh bàn ngang',-9),('0°',0),('Trái 90°',-90),('Phải 90°',90)]:
            button=QPushButton(title);button.clicked.connect(lambda checked=False,a=angle:self.controls['scene_rotation'].setValue(a));qr.addWidget(button)
        vf.addRow('',quick)
        presets=QWidget();pr=QHBoxLayout(presets);pr.setContentsMargins(0,0,0,0)
        for title,values in [('Gọn góc dưới',(320,-9,'bottom_right')),('Rộng, cân bằng',(600,0,'free')),('Dọc mép trái',(340,81,'bottom_left'))]:
            button=QPushButton(title);button.clicked.connect(lambda checked=False,v=values:self.scene_preset(*v));pr.addWidget(button)
        vf.addRow('Bố cục nhanh',presets)
        self.dock=QComboBox()
        for title,key in [('Tự do','free'),('Góc dưới phải','bottom_right'),('Góc dưới trái','bottom_left'),('Góc trên phải','top_right'),('Góc trên trái','top_left')]:self.dock.addItem(title,key)
        self.dock.setCurrentIndex(max(0,self.dock.findData(owner.prefs['dock'])));vf.addRow('Bám mép màn hình',self.dock);self.dock.currentIndexChanged.connect(self.apply)
        hint=QLabel('Ctrl + cuộn chuột: thu/phóng · Alt + cuộn: xoay. Kéo PIRB để di chuyển cả cảnh. Cảnh tự giới hạn kích thước để vừa màn hình.');hint.setObjectName('hint');hint.setWordWrap(True);vf.addRow(hint)
        appearance=QWidget();form=QFormLayout(appearance);self.add_scroll_tab(tabs,appearance,'Giao diện')
        self.section(form,'Mặt bàn','Chọn một khung cảnh hoặc dùng hình ảnh của riêng bạn.')
        self.skin=QComboBox();self.skin.setIconSize(QSize(84,48))
        for title,key in SKINS:
            path=owner.root/'assets'/'backgrounds'/(key+'.jpg');self.skin.addItem(QIcon(str(path)),title,key)
        if owner.prefs['custom_skin']:self.skin.addItem('Ảnh của bạn','custom')
        self.skin.setCurrentIndex(max(0,self.skin.findData(owner.prefs['skin'])));form.addRow('Nền mặt bàn',self.skin)
        self.rotation=QComboBox()
        for title,angle in [('Về phía PIRB · 180°',180),('Về phía người xem · 0°',0),('Xoay 90°',90),('Xoay 270°',270)]:self.rotation.addItem(title,angle)
        self.rotation.setCurrentIndex(max(0,self.rotation.findData(owner.prefs['skin_rotation'])));form.addRow('Hướng ảnh mặt bàn',self.rotation);self.rotation.currentIndexChanged.connect(self.apply)
        choose=QPushButton('Chọn ảnh từ máy…');choose.clicked.connect(self.choose_image);form.addRow('',choose)
        pyth=QPushButton('Dùng nền Pyth Classic');pyth.clicked.connect(self.use_pyth_skin);form.addRow('',pyth)
        self.slider(form,'Độ sáng ảnh','brightness',20,100,'%')
        self.slider(form,'Phóng ảnh','zoom',100,220,'%')
        self.slider(form,'Dịch ảnh ngang','pan_x',-100,100,'')
        self.slider(form,'Dịch ảnh dọc','pan_y',-100,100,'')
        self.section(form,'Dáng vẻ & cảm xúc','Điều chỉnh tư thế và cá tính của PIRB.')
        self.slider(form,'Kích thước PIRB','bird_scale',100,120,'%')
        self.slider(form,'Nghiêng trái / phải','bird_tilt',-18,18,'°')
        self.slider(form,'PIRB sang trái / phải','bird_x',-100,100,'')
        self.slider(form,'PIRB lên / xuống','bird_y',-30,30,'')
        reset=QPushButton('Đặt lại tư thế PIRB');reset.clicked.connect(self.reset_pose);form.addRow('',reset)
        self.expression_mode=QComboBox()
        for title,key in [('Tự động','auto'),('Bình thản','calm'),('Vui vẻ','happy'),('Tập trung','focused'),('Buồn ngủ','sleepy'),('Nháy mắt','wink')]:self.expression_mode.addItem(title,key)
        self.expression_mode.setCurrentIndex(max(0,self.expression_mode.findData(owner.prefs['expression'])));form.addRow('Biểu cảm',self.expression_mode);self.expression_mode.currentIndexChanged.connect(self.apply)
        demo=QPushButton('Xem thử các biểu cảm');demo.clicked.connect(lambda:owner.expression.demo(time.monotonic()));form.addRow('',demo)
        self.section(form,'Ánh sáng & hiệu ứng','Tạo điểm nhấn cho từng lần gõ phím.')
        self.rgb=QComboBox()
        for title,key in [('Tím dịu','purple'),('Cầu vồng chậm','rainbow'),('Tắt đèn','off')]:self.rgb.addItem(title,key)
        self.rgb.setCurrentIndex(max(0,self.rgb.findData(owner.prefs['rgb'])));form.addRow('Đèn bàn phím',self.rgb)
        self.rgb.currentIndexChanged.connect(self.apply);self.skin.currentIndexChanged.connect(self.apply)
        self.effect_level=QComboBox()
        for title,key in [('Tinh tế','soft'),('Rực rỡ','vivid'),('Tắt hiệu ứng','off')]:self.effect_level.addItem(title,key)
        self.effect_level.setCurrentIndex(max(0,self.effect_level.findData(owner.prefs['effects'])));form.addRow('Hiệu ứng tương tác',self.effect_level);self.effect_level.currentIndexChanged.connect(self.apply)
        sound=QWidget();sf=QFormLayout(sound);self.add_scroll_tab(tabs,sound,'Âm thanh')
        self.section(sf,'Thanh âm của PIRB','Chọn tiếng phím và cân chỉnh âm lượng theo ý bạn.')
        self.pack=QComboBox()
        for title,key in PACKS:self.pack.addItem(title,key)
        self.pack.setCurrentIndex(max(0,self.pack.findData(owner.prefs['sound_pack'])));sf.addRow('Mẫu tiếng phím',self.pack);self.pack.currentIndexChanged.connect(self.apply)
        self.section(sf,'Âm thanh của bạn','Nhập WAV PCM tối đa 3 giây, dưới 8 MB. Phím chưa gán dùng âm phím thường; chuột chưa gán dùng Thock.')
        self.sound_slot=QComboBox()
        for title,filename in SOUND_SLOTS:self.sound_slot.addItem(title,filename)
        sf.addRow('Loại phím / chuột',self.sound_slot)
        self.sound_status=QLabel();self.sound_status.setWordWrap(True);self.sound_status.setProperty('dynamic_text',True);sf.addRow(self.sound_status)
        custom_buttons=QWidget();custom_row=QHBoxLayout(custom_buttons);custom_row.setContentsMargins(0,0,0,0)
        for title,callback in [('Chọn WAV…',self.choose_sound),('Nghe âm đã chọn',lambda:owner.audio.preview_slot(self.sound_slot.currentData())),('Bỏ âm riêng',self.clear_sound)]:
            button=QPushButton(title);button.clicked.connect(callback);custom_row.addWidget(button)
        sf.addRow(custom_buttons)
        reset_audio=QPushButton('Khôi phục âm Thock mặc định');reset_audio.clicked.connect(self.reset_sounds);sf.addRow(reset_audio)
        self.sound_slot.currentIndexChanged.connect(self.refresh_sound_status)
        for label,key in [('Tiếng bàn phím','keyboard_sound'),('Tiếng click chuột','mouse_sound'),('PIRB gù nhẹ khi nghỉ lâu','pirb_sound')]:
            check=QCheckBox(label);check.setChecked(owner.prefs[key]);self.controls[key]=check;sf.addRow('',check);check.toggled.connect(self.apply)
        self.slider(sf,'Âm lượng phím','keyboard_volume',0,100,'%')
        self.slider(sf,'Âm lượng chuột','mouse_volume',0,100,'%')
        self.slider(sf,'Âm lượng PIRB','pirb_volume',0,100,'%')
        buttons=QWidget();row=QHBoxLayout(buttons);row.setContentsMargins(0,0,0,0)
        for title,fn in [('Nghe thử phím',owner.audio.preview),('Click thử',lambda:owner.audio.mouse(True)),('Nghe PIRB',lambda:owner.audio.bird(True))]:
            button=QPushButton(title);button.clicked.connect(fn);row.addWidget(button)
        sf.addRow('',buttons)
        note=QLabel('Âm phím mô phỏng switch cơ. Tiếng gù minh họa, không phải âm thanh chính thức của PIRB.');note.setWordWrap(True);sf.addRow(note)
        if not owner.audio.available:
            note=QLabel('Chưa tìm thấy đầu ra âm thanh trong môi trường hiện tại. Các tùy chọn vẫn được lưu.');note.setWordWrap(True);sf.addRow(note)
        for note in sound.findChildren(QLabel):
            if note.wordWrap():note.setObjectName('hint')
        updates=QWidget();uf=QFormLayout(updates);self.add_scroll_tab(tabs,updates,'Cập nhật')
        self.section(uf,'Luôn sẵn sàng với bản mới','Python đã có sẵn trong bộ cài. Bạn không cần tải hoặc cài Python riêng.')
        uf.addRow('Phiên bản hiện tại',QLabel(VERSION))
        for title,key in [('Tự kiểm tra khi mở app và mỗi 6 giờ','check_updates'),('Nhận thông báo bản thử nghiệm','include_prereleases')]:
            check=QCheckBox(title);check.setChecked(owner.prefs[key]);self.controls[key]=check;uf.addRow(check);check.toggled.connect(self.apply)
        note=QLabel('Khi có bản mới, PIRB sẽ hỏi trước. Chỉ khi bạn đồng ý, app mới tải bộ cài, kiểm tra SHA256 và mở trình cài đặt.');note.setWordWrap(True);note.setObjectName('hint');uf.addRow(note)
        self.update_status=QLabel();self.update_status.setWordWrap(True);self.update_status.setProperty('dynamic_text',True);uf.addRow(self.update_status)
        self.check_update_button=QPushButton('Kiểm tra cập nhật ngay');self.check_update_button.clicked.connect(lambda:owner.updater.check(manual=True));uf.addRow(self.check_update_button)
        owner.updater.statusChanged.connect(self.refresh_update_status)
        footer=QHBoxLayout();saved=QLabel('Mọi thay đổi được lưu tự động');saved.setObjectName('hint');footer.addWidget(saved);footer.addStretch()
        close=QPushButton('Hoàn tất');close.setObjectName('primary');close.clicked.connect(self.close);footer.addWidget(close);layout.addLayout(footer)
        screen=self.screen().availableGeometry();self.resize(min(self.width(),screen.width()-24),min(self.height(),screen.height()-48))
        self.ready=True;self.retranslate_ui();self.language.currentIndexChanged.connect(self.change_language);QTimer.singleShot(50,self.update_preview)
        self.preview_timer=QTimer(self);self.preview_timer.timeout.connect(lambda:self.update_preview() if self.isVisible() else None);self.preview_timer.start(150)
    def text(self,source):
        return translate(source,self.owner.prefs.get('language','vi'))
    def resizeEvent(self,event):
        super().resizeEvent(event)
        # Windows fonts need more room than the Linux offscreen font metrics.
        # Stack labels over fields on narrow windows instead of clipping rows.
        policy=(QFormLayout.RowWrapPolicy.WrapAllRows if self.width()<720
                else QFormLayout.RowWrapPolicy.WrapLongRows)
        for area in self.findChildren(QScrollArea):
            page=area.widget()
            if page is not None and isinstance(page.layout(),QFormLayout):page.layout().setRowWrapPolicy(policy)
    def retranslate_ui(self):
        """Update text in place so sliders, scroll positions and item data survive."""
        self.setWindowTitle(self.text('Pirb Desk · Tùy chỉnh')+' · '+VERSION)
        for widget in self.findChildren(QWidget):
            if isinstance(widget,(QLabel,QPushButton,QCheckBox)):
                if widget is self.preview or widget.objectName()=='value' or widget.property('dynamic_text'):continue
                source=widget.property('source_text')
                if source is None:source=widget.text();widget.setProperty('source_text',source)
                widget.setText(self.text(source))
            elif isinstance(widget,QComboBox) and widget is not self.language:
                for i in range(widget.count()):
                    source=widget.itemData(i,Qt.ItemDataRole.UserRole+1)
                    if source is None:source=widget.itemText(i);widget.setItemData(i,source,Qt.ItemDataRole.UserRole+1)
                    widget.setItemText(i,self.text(source))
            elif isinstance(widget,QTabWidget):
                for i in range(widget.count()):
                    page=widget.widget(i);source=page.property('source_title')
                    if source is None:source=widget.tabText(i);page.setProperty('source_title',source)
                    widget.setTabText(i,self.text(source))
            if isinstance(widget,QSlider):
                source=widget.property('source_accessible_name')
                if source is None:source=widget.accessibleName();widget.setProperty('source_accessible_name',source)
                widget.setAccessibleName(self.text(source))
        self.refresh_update_status();self.refresh_sound_status();self.rotation.setEnabled(self.owner.prefs['skin']!='pyth_classic')
    def refresh_update_status(self):
        updater=self.owner.updater
        self.update_status.setText(self.text(updater.status).format(**updater.status_values))
        self.check_update_button.setEnabled(not updater.busy)
    def change_language(self):
        prefs=dict(self.owner.prefs);prefs['language']=self.language.currentData()
        self.owner.apply_preferences(prefs);self.retranslate_ui()
    def add_scroll_tab(self,tabs,widget,title):
        widget.setObjectName('tabPage');form=widget.layout();form.setContentsMargins(20,12,20,20);form.setHorizontalSpacing(18);form.setVerticalSpacing(13);form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        area=QScrollArea();area.setFrameShape(QFrame.Shape.NoFrame);area.setWidgetResizable(True);area.setWidget(widget);tabs.addTab(area,title)
    def section(self,form,title,description):
        heading=QLabel(title);heading.setObjectName('sectionTitle');form.addRow(heading)
        note=QLabel(description);note.setObjectName('sectionNote');note.setWordWrap(True);form.addRow(note)
    def slider(self,form,title,key,lo,hi,suffix):
        holder=QWidget();row=QHBoxLayout(holder);row.setContentsMargins(0,0,0,0)
        slider=QSlider(Qt.Orientation.Horizontal);slider.setAccessibleName(title);slider.setRange(lo,hi);slider.setValue(self.owner.prefs[key]);label=QLabel(str(slider.value())+suffix);label.setObjectName('value');label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setFixedWidth(62)
        slider.valueChanged.connect(lambda value:label.setText(str(value)+suffix));slider.valueChanged.connect(self.apply)
        row.addWidget(slider);row.addWidget(label);form.addRow(title,holder);self.controls[key]=slider;self.value_labels[key]=(label,suffix)
    def apply(self,*args):
        if not self.ready:return
        prefs=dict(self.owner.prefs)
        for key,widget in self.controls.items():prefs[key]=widget.isChecked() if isinstance(widget,QCheckBox) else widget.value()
        prefs['dock']=self.dock.currentData();prefs['effects']=self.effect_level.currentData()
        prefs['skin_rotation']=self.rotation.currentData();prefs['expression']=self.expression_mode.currentData()
        prefs['skin']=self.skin.currentData();prefs['rgb']=self.rgb.currentData();prefs['sound_pack']=self.pack.currentData()
        self.owner.apply_preferences(prefs);self.rotation.setEnabled(prefs['skin']!='pyth_classic');self.refresh_sound_status();self.update_preview()
    def scene_preset(self,width,angle,dock):
        self.ready=False;self.controls['scene_width'].setValue(width);self.controls['scene_rotation'].setValue(angle);self.dock.setCurrentIndex(self.dock.findData(dock));self.ready=True;self.apply()
    def reset_pose(self):
        self.ready=False
        for key,value in [('bird_scale',115),('bird_tilt',0),('bird_x',0),('bird_y',0)]:self.controls[key].setValue(value)
        self.ready=True;self.apply()
    def use_pyth_skin(self):
        self.ready=False
        self.skin.setCurrentIndex(self.skin.findData('pyth_classic'))
        for key,value in [('brightness',90),('zoom',100),('pan_x',0),('pan_y',0)]:self.controls[key].setValue(value)
        self.ready=True;self.apply()
    def refresh_sound_status(self,*args):
        if not hasattr(self,'sound_status'):return
        prefs=self.owner.prefs;path=prefs.get('custom_sounds',{}).get(self.sound_slot.currentData(),'')
        if prefs['sound_pack']!='custom':message=self.text('Đang dùng mẫu âm có sẵn. Chọn WAV để bật âm thanh của bạn.')
        elif path and Path(path).is_file():message=self.text('Âm riêng: {name}').format(name=Path(path).stem.rsplit('-',1)[0][:48]+'.wav')
        elif path:message=self.text('Không tìm thấy âm riêng. Đang dùng âm thay thế.')
        else:message=self.text('Chưa gán âm riêng. Đang dùng âm thay thế.')
        self.sound_status.setText(message)
    def choose_sound(self):
        path,_=QFileDialog.getOpenFileName(self,self.text('Chọn âm bàn phím hoặc chuột'),'',self.text('Âm thanh WAV (*.wav)'))
        if not path:return
        try:stored=import_sound(path)
        except (OSError,ValueError) as error:
            message=str(error) if isinstance(error,ValueError) else 'Không nhập được âm thanh. Hãy kiểm tra tệp và thử lại.'
            QMessageBox.warning(self,self.text('Không nhập được âm thanh'),self.text(message));return
        prefs=dict(self.owner.prefs);sounds=dict(prefs.get('custom_sounds',{}));sounds[self.sound_slot.currentData()]=stored
        prefs.update(custom_sounds=sounds,sound_pack='custom');self.owner.apply_preferences(prefs)
        self.pack.blockSignals(True);self.pack.setCurrentIndex(self.pack.findData('custom'));self.pack.blockSignals(False)
        self.refresh_sound_status()
    def clear_sound(self):
        prefs=dict(self.owner.prefs);sounds=dict(prefs.get('custom_sounds',{}));sounds.pop(self.sound_slot.currentData(),None)
        prefs['custom_sounds']=sounds;self.owner.apply_preferences(prefs);self.refresh_sound_status()
    def reset_sounds(self):
        self.owner.apply_preferences(dict(self.owner.prefs,custom_sounds={},sound_pack='thock'))
        self.pack.blockSignals(True);self.pack.setCurrentIndex(self.pack.findData('thock'));self.pack.blockSignals(False);self.refresh_sound_status()
    def choose_image(self):
        path,_=QFileDialog.getOpenFileName(self,self.text('Chọn ảnh nền mặt bàn'),'',self.text('Ảnh (*.png *.jpg *.jpeg *.webp)'))
        if not path:return
        try:stored=import_skin(path)
        except (OSError,ValueError) as e:QMessageBox.warning(self,self.text('Không mở được ảnh'),self.text(str(e)));return
        prefs=dict(self.owner.prefs);prefs['custom_skin']=stored;prefs.update(skin='custom',zoom=100,pan_x=0,pan_y=0)
        self.owner.apply_preferences(prefs)
        self.ready=False
        if self.skin.findData('custom')<0:self.skin.addItem('Ảnh của bạn','custom')
        self.skin.setCurrentIndex(self.skin.findData('custom'))
        for key in ('zoom','pan_x','pan_y'):self.controls[key].setValue(prefs[key])
        self.ready=True;self.retranslate_ui();self.update_preview()
    def update_preview(self):
        for key in ('scene_width','scene_rotation'):
            slider=self.controls[key]
            if not slider.isSliderDown() and slider.value()!=self.owner.prefs[key]:
                slider.blockSignals(True);slider.setValue(self.owner.prefs[key]);slider.blockSignals(False)
                label,suffix=self.value_labels[key];label.setText(str(slider.value())+suffix)
        if self.dock.currentData()!=self.owner.prefs['dock']:
            self.dock.blockSignals(True);self.dock.setCurrentIndex(self.dock.findData(self.owner.prefs['dock']));self.dock.blockSignals(False)
        image=self.owner.grab();self.preview.setPixmap(image.scaled(max(1,self.preview.width()-8),self.preview.height()-8,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
