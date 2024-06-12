from PyQt5 import QtWidgets, QtCore, QtGui,uic
import ctypes, sys, random, flappyqrc

UI_FILE = 'flappy.ui'

class Flappy(QtWidgets.QMainWindow):
    def __init__(self):
        super(Flappy, self).__init__()
        uic.loadUi(UI_FILE, self)
        user32 = ctypes.windll.user32
        self.screen_width = user32.GetSystemMetrics(0)
        self.jumpCondition = False
        self.screen_height = user32.GetSystemMetrics(1) - user32.GetSystemMetrics(2)
        self.label.setGeometry(((int(self.screen_width/2)) - int(self.label.width() /2)), self.label.y(), self.label.width(), self.label.height())
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.frame.move(QtCore.QPoint(200, 90))
        self.frame_2.move(QtCore.QPoint(int(self.screen_width /2) - int(self.frame_2.width() /2), int(self.screen_height /2) - int(self.frame_2.height() /2)))
        self.score = 0
        self.cJump = True
        pixmap = QtGui.QPixmap(":/pics/icons8-play-50.png")
        self.playButton = ClickableLabel(self.frame_2)
        self.playButton.setPixmap(pixmap)
        self.playButton.setAlignment(QtCore.Qt.AlignCenter)
        self.playButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.playButton.setGeometry(170, 210, 211, 111)
        self.playButton.setStyleSheet("QLabel{background-color: rgb(255, 255, 255);}QLabel:hover{background-color: rgba(255, 255, 255, 90%);}")
        self.playButton.clicked.connect(self.StartGame)
        self.exitButton = ClickableLabel(self.frame_2)
        self.exitButton.setText("Exit")
        self.exitButton.setAlignment(QtCore.Qt.AlignCenter)
        self.exitButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.exitButton.setGeometry((self.playButton.x() + int(self.playButton.width()/2) - int(self.exitButton.width() /2)), 325, 100,50)
        self.exitButton.setStyleSheet("QLabel{background-color: rgb(255, 255, 255);}QLabel:hover{background-color: rgba(255, 255, 255, 90%);}")
        self.exitButton.clicked.connect(self.close)
        self.gravityWorker = Gravity()
        self.gravityWorker.getPos.connect(self.getPos)
        self.gravityWorker.applyGravity.connect(self.applyGravity)
        self.gravityWorker.applyJump.connect(self.applyJump)
        self.gravityWorker.start()
        self.jumpWorker = Jump()
        self.jumpWorker.applyJump.connect(self.applyJump)
        self.jumpWorker.stopJump.connect(self.stopJump)
        self.jumpWorker.start()
        self.columnWorker = Columns()
        self.columnWorker.getColumPosSignal.connect(self.getColumnPos)
        self.columnWorker.moveColumsSignal.connect(self.moveColumn)
        self.columnWorker.createColumnsSignal.connect(self.createColumn)
        self.columnWorker.detectcollisionSignal.connect(self.detectCollision)
        self.columnWorker.start()
        self.createColumnsAtStart()
        #self.createColumn()
    
    def point_inside_rect(self, point, rect):
        return rect.x() <= point.x() <= rect.x() + rect.width() and \
            rect.y() <= point.y() <= rect.y() + rect.height()

    def check_collision(self, frame1, frame2):
        for corner in [frame1.topLeft(), frame1.topRight(), frame1.bottomLeft(), frame1.bottomRight()]:
            if self.point_inside_rect(corner, frame2):
                return True
            if corner.y() >= self.screen_height or corner.y() <= 0:
                return True
        return False

    def detectCollision(self):
        try:
            playerGeometry = self.frame.geometry()
            nextTopColumn = Column.ColumnsList[0].geometry()
            nextBottomColumn = Column.ColumnsList[1].geometry()
            collision_detected_top = self.check_collision(playerGeometry, nextTopColumn)
            collision_detected_bottom = self.check_collision(playerGeometry, nextBottomColumn)

            if collision_detected_top or collision_detected_bottom:
                self.death()
        except:
            self.columnWorker.createColumns()

    def clearColumns(self):
        for column in Column.ColumnsList:
            column.deleteLater()
        Column.ColumnsList.clear()
    
    def createColumnsAtStart(self):
        for i in range(4):
            x = self.screen_width - (350 * i)
            column = Column("", x, startHeight=self.columnWorker.getRandomHeight(self.screen_height), passed= False, parent = self)
            bottom = column.y() + column.height()
            column2 = Column("", x,startHeight=bottom + 230, parent = self,top=False)
            column.lower()
            column2.lower()
            self.label.raise_()
        # Reversed the list because it spawn from left to right and reversing it doesnt break the collision detection
        Column.ColumnsList.reverse()

    def death(self):
        self.columnWorker.stopAll()
        self.gravityWorker.stopAll()
        self.jumpWorker.isDead = True
        self.clearColumns()
        self.createColumnsAtStart()
        self.frame_2.show()
        self.label_2.setText(f"Your Score: {self.score}")
    
    def StartGame(self):
        self.frame_2.hide()
        self.score = 0
        self.label.setText(str(self.score))
        self.frame.move(QtCore.QPoint(200, 90))
        self.gravityWorker.accumulated_gravity = 0 
        self.columnWorker.startAll()
        self.gravityWorker.startAll()
        self.jumpWorker.isDead = False
    def keyPressEvent(self, event):
        match event.key():
            case QtCore.Qt.Key_Space:
                if self.cJump and not self.jumpWorker.isDead:
                    self.jump()
                    self.cJump = False
    def keyReleaseEvent(self, event):
        match event.key():
            case QtCore.Qt.Key_Space:
                if not event.isAutoRepeat() and not self.jumpWorker.isDead:
                    self.cJump = True
    def getPos(self):
        self.gravityWorker.gravity(self.frame.y())

    def getColumnPos(self):
        for i in reversed(Column.ColumnsList):
            self.columnWorker.moveColums(i.x(), i)
    
    def moveColumn(self,pos: int, widget):
        if widget.passed is not None:
            if widget.x() <= 200 and not widget.passed:
                self.score += 1
                self.label.setText(str(self.score))
                widget.passed = True
        if widget.x() <= -100:
            Column.ColumnsList.remove(widget)
            widget.deleteLater()
        else:
            widget.move(QtCore.QPoint(pos, widget.y()))

    def applyGravity(self, pos: int):
        if not self.jumpCondition:
            self.frame.move(QtCore.QPoint(self.frame.x(), pos))
    
    def createColumn(self):
        column = Column("", self.screen_width,startHeight=self.columnWorker.getRandomHeight(self.screen_height), passed= False, parent = self)
        bottom = column.y() + column.height()
        column2 = Column("", self.screen_width,startHeight=bottom + 230, parent = self,top=False )
        column.lower()
        column2.lower()
        self.label.raise_()
    
    def jump(self):
        self.jumpCondition = True
        self.jumpWorker.ru(self.frame.y())
    def stopJump(self):
        self.jumpCondition = False
        self.gravityWorker.accumulated_gravity = -10
    
    def applyJump(self, pos: int):
        self.frame.move(QtCore.QPoint(self.frame.x(), pos))

    def closeEvent(self, event):
        event.accept()
        

class Gravity(QtCore.QThread):
    getPos = QtCore.pyqtSignal()
    applyGravity = QtCore.pyqtSignal(int)
    applyJump = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.accumulated_gravity = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.GetPos)
        
    def startAll(self):
        self.timer.start(20)
    
    def stopAll(self):
        self.timer.stop()

    def GetPos(self):
        self.getPos.emit()
    def gravity(self, pos: int):
        self.accumulated_gravity += 2
        pos += self.accumulated_gravity
        self.applyGravity.emit(pos)
    
class Jump(QtCore.QThread):
    applyJump = QtCore.pyqtSignal(int)
    stopJump = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.accumulated_jump = 0
        self.running = False
        self.isDead = True
    
    def ru(self, pos: int):
        if not self.isDead:
            self.original_y = pos
            self.accumulated_jump = 0
            self.start_timer()

    def start_timer(self):
        if not self.running:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.jump)
            self.timer.start(20)
            self.running = True

    def jump(self):
        if not self.isDead:
            self.accumulated_jump += 5
            self.original_y -= self.accumulated_jump
            self.applyJump.emit(self.original_y)
            if self.accumulated_jump >= 25:
                self.timer.stop()
                self.running = False
                self.accumulated_jump = 0
                self.stopJump.emit()

class Column(QtWidgets.QFrame):
    ColumnsList = []
    top_image = QtGui.QImage(":/pics/top-min.png")
    bottom_image = QtGui.QImage(":/pics/bottom-min.png")
    def __init__(self, stylesheet: str, screenWidth: int, startHeight: int = 0, height: int = 1000, passed = None, parent = None, top = True):
        super().__init__(parent)
        self.columnHeight = startHeight
        self.passed = passed
        self.top = top
        self.setStyleSheet(stylesheet)
        self.setGeometry(screenWidth, self.columnHeight, 120, height)
        self.show()
        self.ColumnsList.append(self)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.top:
            painter.drawImage(self.rect(), self.top_image)
        else:
            painter.drawImage(self.rect(), self.bottom_image)
class Columns(QtCore.QThread):
    moveColumsSignal = QtCore.pyqtSignal(int, Column)
    getColumPosSignal = QtCore.pyqtSignal()
    createColumnsSignal = QtCore.pyqtSignal()
    detectcollisionSignal = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.getColumPos)
        
        self.detecttimer = QtCore.QTimer(self)
        self.detecttimer.timeout.connect(self.detect)
        
        self.createColumnTimer = QtCore.QTimer(self)
        self.createColumnTimer.timeout.connect(self.createColumns)
        
    
    def startAll(self):
        self.timer.start(16)
        self.detecttimer.start(50)
        self.createColumnTimer.start(3500)
    
    def stopAll(self):
        self.timer.stop()
        self.detecttimer.stop()
        self.createColumnTimer.stop()
    def detect(self):
        self.detectcollisionSignal.emit()
    
    def createColumns(self):
        self.createColumnsSignal.emit()
    def getColumPos(self):
        self.getColumPosSignal.emit()

    def moveColums(self, pos: int, widget: Column):
        pos -= 2
        self.moveColumsSignal.emit(pos, widget)

    def getRandomHeight(self, screenHeight):
        return random.randint(-1000, -230)

class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()

    
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Flappy()
    window.show()
    sys.exit(app.exec_())


    


if __name__ == "__main__":
    main()