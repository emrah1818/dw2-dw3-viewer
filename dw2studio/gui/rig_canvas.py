"""CPU 3D face picking/rig inspection surface; usable without desktop OpenGL."""
import numpy as np
from PyQt6.QtCore import Qt,QPointF,QRectF,pyqtSignal
from PyQt6.QtGui import QColor,QPainter,QPen,QPolygonF,QPainterPath,QTransform
from PyQt6.QtWidgets import QWidget

COLORS=['#55b4f4','#ee9460','#73ce9c','#c18ce8','#e5ca68','#ed799b','#64d2ce','#ada9f1']

class RigCanvas(QWidget):
    selectionChanged=pyqtSignal()
    def __init__(self,project,parent=None):
        super().__init__(parent);self.project=project;self.selected=set();self.yaw=.45;self.pitch=-.15;self.zoom=1.;self.start=None;self.end=None;self.dragging=False;self.texture=None;self.show_texture=False;self.show_reference=False;self.active_bone=0;self.reference_parts=[]
        self.setMinimumSize(380,280);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        import struct
        from ..core.rig_animation import D
        for part in project.model.parts:
            vertices=np.array([struct.unpack_from('<hhh',project.original,part.vertices+6+i*6) for i in range(part.vertex_count)])@D
            faces=[]
            for vs,ns,uv,clut,stp in part.primitives:
                for order in ((2,1,0),(1,2,3)) if len(vs)==4 else ((2,1,0),):faces.append([vs[j] for j in order])
            self.reference_parts.append(vertices[np.asarray(faces)])
        self.triangles=project.source_vertices()[project.mesh.face_indices];self.bones=project.binding_world();self.center=self.triangles.reshape(-1,3).mean(0);self.span=max(np.ptp(self.triangles.reshape(-1,3),axis=0).max(),1.)
    def set_pose(self,triangles,bones):self.triangles=triangles;self.bones=bones;self.update()
    def reset_camera(self):
        self.center=(self.triangles.reshape(-1,3).min(0)+self.triangles.reshape(-1,3).max(0))/2;self.span=max(np.ptp(self.triangles.reshape(-1,3),axis=0).max(),1.);self.zoom=1.;self.update()
    def project_points(self,points):
        cy,sy=np.cos(self.yaw),np.sin(self.yaw);cx,sx=np.cos(self.pitch),np.sin(self.pitch)
        rot=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
        p=(np.asarray(points)-self.center)@rot;factor=min(self.width(),self.height())*.75/self.span*self.zoom
        return np.stack([self.width()/2+p[...,0]*factor,self.height()/2-p[...,1]*factor,p[...,2]],axis=-1)
    def paintEvent(self,event):
        painter=QPainter(self);painter.fillRect(self.rect(),QColor('#0b1525'));painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        projected=self.project_points(self.triangles);self._projected=projected
        for i in np.argsort(projected[:,:,2].mean(1)):
            polygon=QPolygonF([QPointF(float(x),float(y)) for x,y,z in projected[i]])
            bone=int(self.project.assignment[i]);color=QColor(COLORS[bone%len(COLORS)] if bone>=0 else '#6b778a')
            color.setAlpha(150);painter.setBrush(color);painter.setPen(QPen(QColor('#21324c'),.6));painter.drawPolygon(polygon)
            face=self.project.mesh.faces[i]
            if self.show_texture and self.texture is not None and all(index>=0 for index in face.uv):
                uv=np.array([self.project.mesh.texcoords[index] for index in face.uv]);src=np.c_[uv[:,0]*127,(1-uv[:,1])*(223 if self.project.uv_mode=='fit224' else 255),np.ones(3)]
                try:
                    coeff=np.linalg.solve(src,projected[i,:,:2]);transform=QTransform(coeff[0,0],coeff[0,1],coeff[1,0],coeff[1,1],coeff[2,0],coeff[2,1])
                    painter.save();path=QPainterPath();path.addPolygon(polygon);painter.setClipPath(path);painter.setTransform(transform);painter.drawImage(0,0,self.texture);painter.restore()
                except np.linalg.LinAlgError:pass
            if i in self.selected:
                painter.setBrush(QColor(255,212,64,100));painter.setPen(QPen(QColor('#ffe067'),1.4));painter.drawPolygon(polygon)
        if self.show_reference:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for bone,triangles in enumerate(self.reference_parts):
                local=np.concatenate([triangles,np.ones((*triangles.shape[:2],1))],axis=2)
                world=(local@self.bones[bone].T)[:,:,:3];outline=self.project_points(world)
                painter.setPen(QPen(QColor('#fff0a0' if bone==self.active_bone else '#59728d'),1.6 if bone==self.active_bone else .6))
                for triangle in outline:painter.drawPolygon(QPolygonF([QPointF(float(x),float(y)) for x,y,z in triangle]))
        joints=self.project_points(self.bones[:,:3,3]);painter.setPen(QPen(QColor('#fff1ad'),2))
        for i,parent in enumerate(self.project.parents):
            x,y,z=joints[i]
            if parent>=0:painter.drawLine(QPointF(float(x),float(y)),QPointF(float(joints[parent,0]),float(joints[parent,1])))
            painter.setBrush(QColor(COLORS[i%len(COLORS)]));painter.drawEllipse(QPointF(float(x),float(y)),4,4);painter.drawText(QPointF(float(x+5),float(y-5)),str(i))
        if self.start is not None and self.end is not None:
            painter.setBrush(QColor(80,160,255,40));painter.setPen(QPen(QColor('#7dcaff'),1));painter.drawRect(QRectF(self.start,self.end).normalized())
        painter.setPen(QColor('#bdcce2'));painter.drawText(12,self.height()-13,'Links: Fläche/Rechteck · Strg: ergänzen · Rechts ziehen: drehen · Rad: Zoom')
    def mousePressEvent(self,event):
        self.setFocus();self.last=event.position();self.dragging=event.button()==Qt.MouseButton.RightButton
        if event.button()==Qt.MouseButton.LeftButton:self.start=event.position();self.end=event.position();self.update()
    def mouseMoveEvent(self,event):
        if self.dragging:
            delta=event.position()-self.last;self.yaw+=delta.x()*.009;self.pitch+=delta.y()*.009;self.last=event.position();self.update()
        elif self.start is not None:self.end=event.position();self.update()
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.RightButton:self.dragging=False;return
        if self.start is None:return
        rect=QRectF(self.start,event.position()).normalized();projected=self.project_points(self.triangles);hits=[]
        if rect.width()+rect.height()<8:
            point=np.array([event.position().x(),event.position().y()])
            for i,triangle in enumerate(projected):
                matrix=np.c_[triangle[:,:2],np.ones(3)].T
                try:
                    weights=np.linalg.solve(matrix,np.r_[point,1])
                    if weights.min()>=-1e-6:hits.append((float(weights@triangle[:,2]),i))
                except np.linalg.LinAlgError:pass
            chosen={max(hits)[1]} if hits else set()
        else:chosen={i for i,triangle in enumerate(projected) if rect.contains(QPointF(float(triangle[:,0].mean()),float(triangle[:,1].mean())))}
        if event.modifiers()&Qt.KeyboardModifier.ControlModifier:self.selected^=chosen
        elif event.modifiers()&Qt.KeyboardModifier.ShiftModifier:self.selected|=chosen
        else:self.selected=chosen
        self.start=self.end=None;self.selectionChanged.emit();self.update()
    def wheelEvent(self,event):self.zoom=np.clip(self.zoom*(1.12 if event.angleDelta().y()>0 else 1/1.12),.1,10);self.update()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_A and event.modifiers()&Qt.KeyboardModifier.ControlModifier:self.selected=set(range(len(self.project.mesh.faces)))
        elif event.key()==Qt.Key.Key_Escape:self.selected.clear()
        else:return super().keyPressEvent(event)
        self.selectionChanged.emit();self.update()
