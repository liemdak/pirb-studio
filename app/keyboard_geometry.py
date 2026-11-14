from PySide6.QtCore import QRectF
def keyboard_layout():
    keys=[]
    def add(label,vk,x,y,w=1,h=1): keys.append((label,vk,QRectF(x,y,w,h)))
    for label,vk,x in [('Esc',27,0)]+[(f'F{i}',111+i,1.5+(i-1)*1.05+(0.4 if i>4 else 0)+(0.4 if i>8 else 0)) for i in range(1,13)]+[('Prt',44,15.6),('Scr',145,16.65),('Pause',19,17.7)]: add(label,vk,x,0)
    rows=[ [('`',192,1)]+[(str(i),48+i,1) for i in range(1,10)]+[('0',48,1),('-',189,1),('=',187,1),('Back',8,2)],
    [('Tab',9,1.5)]+[(c,ord(c),1) for c in 'QWERTYUIOP']+[('[',219,1),(']',221,1),('\\',220,1.5)],
    [('Caps',20,1.75)]+[(c,ord(c),1) for c in 'ASDFGHJKL']+[(';',186,1),("'",222,1),('Enter',13,2.25)],
    [('Shift',160,2.25)]+[(c,ord(c),1) for c in 'ZXCVBNM']+[(',',188,1),('.',190,1),('/',191,1),('Shift',161,2.75)],
    [('Ctrl',162,1.25),('Win',91,1.25),('Alt',164,1.25),('Space',32,6.25),('Alt',165,1.25),('Win',92,1.25),('Menu',93,1.25),('Ctrl',163,1.25)]]
    for r,row in enumerate(rows):
        x=0
        for label,vk,w in row: add(label,vk,x,1.4+r,w); x+=w
    for r,row in enumerate([[('Ins',45),('Home',36),('PgUp',33)],[('Del',46),('End',35),('PgDn',34)]]):
        for c,(label,vk) in enumerate(row): add(label,vk,15.6+c*1.05,1.4+r)
    for label,vk,x,y in [('↑',38,16.65,4.4),('←',37,15.6,5.4),('↓',40,16.65,5.4),('→',39,17.7,5.4)]: add(label,vk,x,y)
    for label,vk,x,y,w,h in [('Num',144,19,1.4,1,1),('/',111,20,1.4,1,1),('*',106,21,1.4,1,1),('-',109,22,1.4,1,1),('+',107,22,2.4,1,2),('Enter',108,22,4.4,1,2),('0',96,19,5.4,2,1),('.',110,21,5.4,1,1)]: add(label,vk,x,y,w,h)
    for r,nums in enumerate(['789','456','123']):
        for c,n in enumerate(nums): add(n,96+int(n),19+c,2.4+r)
    return keys
KEYS=keyboard_layout()
