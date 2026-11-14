"""User preferences and local image imports."""
import json,shutil
from pathlib import Path
from PySide6.QtCore import QStandardPaths,QSize,Qt
from PySide6.QtGui import QImageReader,QPixmap

DEFAULTS={
 'language':'vi',
 'skin':'fuji_sakura','custom_skin':'','brightness':82,'zoom':100,'pan_x':0,'pan_y':0,
 'scene_width':600,'scene_rotation':0,'dock':'free','effects':'soft','bird_scale':115,'bird_tilt':0,'bird_x':0,'bird_y':0,'expression':'auto','skin_rotation':180,'rgb':'purple','keyboard_sound':True,'mouse_sound':True,'pirb_sound':False,
 'sound_pack':'thock','keyboard_volume':25,'mouse_volume':20,'pirb_volume':25,
}
SKINS=[('Núi Phú Sĩ & hoa anh đào','fuji_sakura'),('Khu vườn đền Nhật','temple_garden'),('Thung lũng hoàng hôn','valley_sunset'),('Mặt bàn trơn','none')]
PACKS=[('Thock · trầm, đầm','thock'),('Clicky · tách rõ','clicky'),('Tactile · gọn, nhẹ','tactile')]

def load_preferences(settings):
    result=dict(DEFAULTS)
    try:
        value=json.loads(settings.value('preferences','{}'))
        if isinstance(value,dict):result.update({k:v for k,v in value.items() if k in DEFAULTS})
    except (ValueError,TypeError):pass
    for k,lo,hi in [('scene_width',180,1200),('scene_rotation',-180,180),('brightness',20,100),('zoom',100,220),('pan_x',-100,100),('pan_y',-100,100),('bird_scale',100,120),('bird_tilt',-18,18),('bird_x',-100,100),('bird_y',-30,30),('keyboard_volume',0,100),('mouse_volume',0,100),('pirb_volume',0,100)]:
        try:result[k]=max(lo,min(hi,int(result[k])))
        except (TypeError,ValueError):result[k]=DEFAULTS[k]
    for k in ('keyboard_sound','mouse_sound','pirb_sound'):result[k]=result[k] if isinstance(result[k],bool) else DEFAULTS[k]
    if result['language'] not in ('vi','en'):result['language']='vi'
    if result['dock'] not in ('free','bottom_right','bottom_left','top_right','top_left'):result['dock']='free'
    if result['effects'] not in ('off','soft','vivid'):result['effects']='soft'
    if result['skin_rotation'] not in (0,90,180,270):result['skin_rotation']=180
    if result['expression'] not in ('auto','calm','happy','focused','sleepy','wink'):result['expression']='auto'
    if result['rgb'] not in ('off','purple','rainbow'):result['rgb']='purple'
    if result['sound_pack'] not in ('thock','clicky','tactile'):result['sound_pack']='thock'
    return result

def load_image(path):
    reader=QImageReader(str(path));reader.setAutoTransform(True)
    size=reader.size()
    if size.isValid() and max(size.width(),size.height())>2048:
        reader.setScaledSize(size.scaled(QSize(2048,2048),Qt.AspectRatioMode.KeepAspectRatio))
    im=reader.read()
    if im.isNull():raise ValueError('Không đọc được ảnh. Hãy chọn PNG, JPG hoặc WEBP hợp lệ.')
    return QPixmap.fromImage(im)

def import_skin(path):
    source=Path(path)
    if source.stat().st_size>30*1024*1024:raise ValueError('Hãy chọn ảnh nhỏ hơn 30 MB.')
    load_image(source)
    destination=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    destination.mkdir(parents=True,exist_ok=True)
    target=destination/('custom_desk'+source.suffix.lower())
    if source.resolve()!=target.resolve():shutil.copyfile(source,target)
    return str(target)
