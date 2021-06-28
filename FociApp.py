# -*- coding: utf-8 -*-

#Created on Thu Mar 19 20:03:55 2020


#@author: Tuieng Ren Jie

import sys,time,concurrent.futures
##### Might need to change this if different comp!!! ######
sys.path.append('C://Users//Admin//Anaconda3//envs//RJ//Lib//site-packages') #Get path where modules are installed in

#For image processing
import os,czifile
import sys
import tkinter 
#from aicsimageio import AICSImage
import matplotlib
import skimage  
import numpy
import io
import cv2
import glob
matplotlib.use('WxAgg')
import pandas as pd
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from skimage.morphology import disk
from skimage.filters import threshold_yen, threshold_otsu,threshold_mean, threshold_triangle
import wx,wx.xrc,wx.dataview
import xml.etree.ElementTree as ET #For finding XML Data
from tkinter import filedialog #For specifying folders
############# Functions ########################
def getCentroidArea_Data(label_img):
    props = skimage.measure.regionprops(label_img)
    foci_num = len(props)     #Number of foci based on length of list
    centroidData = [] #Create empty list
    area_Data = 0
    for prop in props:
        cent = list(prop['centroid'])
        cent.reverse()
        centroidData.append(cent)
        area_Data += prop['area']

    return centroidData, area_Data

def drawCircles(ax,centroidData):
    for x,y in centroidData:
        circle = matplotlib.patches.Circle((x,y),20,fill= False,color='white')
        ax.add_patch(circle)
def updateExcel (df, excel_file_name,excel_sheet_name):
    writer = pd.ExcelWriter(f'{excel_file_name}.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name=excel_sheet_name, float_format = "%0.3f")    
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()    

def splitDataRGB(data):
    for x in range(len(data.shape)):
        if data.shape[x]==3:
            num=x
    for y in range(num):
        data=data[0]             #flattening the brackets
    red_data=data[0]
    green_data=data[1]
    blue_data=data[2]
    for z in range(3-num):       #total 4-1 brackets before xyz data everytime and flatten again
        red_data=red_data[0]
        green_data=green_data[0]
        blue_data=blue_data[0]
    final_red=red_data[:,:,:,0]
    final_green=green_data[:,:,:,0]
    final_blue=blue_data[:,:,:,0]
    clean_data=[final_red,final_green,final_blue]
    return clean_data
##################################################.
app = wx.App(False)
# Define a class? of frame?

#%%
        
class imPanel(wx.Panel):
    def __init__(self,parent):        
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.Size( 700,900), 0 )
        self.figure = Figure(figsize = (14.5, 9))
        self.axes = self.figure.add_subplot(111,position=[0,0.025,1,0.95])
        self.axes.axis('off')
        self.canvas = FigureCanvas( self,-1,self.figure)



    def imshow(self,image,cmap='viridis'):
        self.axes.imshow(image,cmap=cmap)
        self.canvas.draw()
        
class textPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.entry = wx.TextCtrl(self, -1)
        

class MainFrame ( wx.Frame ):
    
    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY,title = "Foci App", pos = wx.DefaultPosition, size = wx.Size( 1158,620 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        self.Maximize(True)
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        
        ########### Sizer 1 Overall #################################
        wSizer1 = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )#Overall Sizer
        
        
        ########### Sizer 2: Load File/Folder Buttons ################
        wSizer2 = wx.WrapSizer(wx.HORIZONTAL, wx.WRAPSIZER_DEFAULT_FLAGS)
        
        self.LoadFolderBtn = wx.Button( self, wx.ID_ANY, u"Load Folder", wx.DefaultPosition, wx.DefaultSize, 0 )
        wSizer2.Add( self.LoadFolderBtn, 0, wx.ALL, 5 )
        
        self.LoadFileBtn = wx.Button( self, wx.ID_ANY, u"Load File", wx.DefaultPosition, wx.DefaultSize, 0 )
        wSizer2.Add( self.LoadFileBtn, 0, wx.ALL, 5 )
        
        wSizer1.Add( wSizer2, 1, wx.ALIGN_CENTER, 5 ) #Add sizer2 to sizer 1
        ##################End of Sizer 2 stuffs ######################
        
        ######### Sizer 3: Load file List box, Options box ###########
        wSizer3 = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )

        m_listBox1Choices = []
        self.m_listBox1 = wx.ListBox( self, wx.ID_ANY, wx.Point( -1,-1 ), wx.Size( 300,400 ), m_listBox1Choices, 0 )
        wSizer3.Add( self.m_listBox1, 0, wx.ALL, 5 )
          
 
        threshSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.threshG = textPanel(self)
        self.threshR = textPanel(self)
          
        threshSizer.Add(self.threshG, 0, wx.ALL, 5)
        threshSizer.Add(self.threshR, 0, wx.ALL, 5)
        self.threshG.entry.SetValue(str(1))
        self.threshR.entry.SetValue(str(1))
        wSizer3.Add(threshSizer, 1, wx.ALIGN_CENTER, 5)
          
        label = wx.StaticText(self, -1, 'Green Thresh                   Red Thresh')
        wSizer3.Add(label, flag = wx.ALIGN_CENTER_HORIZONTAL)
        
        fociSizeSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.minFociSize = textPanel(self)
        self.minFociSize.entry.SetValue(str(4))
        fociSizeSizer.Add(self.minFociSize)
        
        label2 = wx.StaticText(self,-1,'Min Foci Size         Max Foci Size')
        
        self.maxFociSize = textPanel(self)
        self.maxFociSize.entry.SetValue(str(20))
        fociSizeSizer.Add(self.maxFociSize)

        wSizer3.Add(fociSizeSizer,1,wx.ALIGN_CENTER,5)
        wSizer3.Add(label2,1,wx.ALIGN_CENTER,1)

        
        optionSizer = wx.WrapSizer(wx.HORIZONTAL, wx.WRAPSIZER_DEFAULT_FLAGS)

        pnlG = wx.Panel(self)
        wx.StaticBox(pnlG,label='Green/53BP1 Options',size=(130,100))
        self.gVcb = wx.CheckBox(pnlG,label='Volume',pos=(15,30))
        self.gIcb = wx.CheckBox(pnlG,label='Intensity',pos=(15,55))
        self.gVcb.SetValue(True)
        optionSizer.Add(pnlG,1,wx.ALIGN_CENTER,5)
        
        pnlR = wx.Panel(self)
        wx.StaticBox(pnlR,label='Red/gH2AX Options',size=(130,100))
        self.rVcb = wx.CheckBox(pnlR,label='Volume',pos=(15,30))
        self.rIcb = wx.CheckBox(pnlR,label='Intensity',pos=(15,55))
        self.rIcb.SetValue(True)
        optionSizer.Add(pnlR,1,wx.ALIGN_CENTER,5)
        
        wSizer3.Add(optionSizer,1,wx.ALIGN_CENTER,5)
      
        wSizer1.Add(wSizer3, 1, 0, 5 )
        
        ##################End of Sizer 3 stuffs ######################
        
        ######### Sizer 4: DisplayImage Sizer, Panel, Slider##########
        DisplayImage = wx.BoxSizer( wx.VERTICAL )
        
        self.ImMaxSize = 700
        self.testPanel = imPanel(self)
        DisplayImage.Add( self.testPanel, 0, wx.ALL, 5 )        
        
        self.imSlider = wx.Slider( self, wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.Size( self.ImMaxSize,-1 ), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_MIN_MAX_LABELS)
        DisplayImage.Add( self.imSlider, 0, wx.ALL, 5 )
        wSizer1.Add( DisplayImage, 1, 0, 5 )
        ##################End of Sizer 4 stuffs ######################
        

        wSizer5 = wx.BoxSizer(wx.VERTICAL)
        ################## ButtonWrap ################################
        ButtonWrap = wx.BoxSizer(wx.HORIZONTAL)
        
        ############### Sizer 6: FociCount/Vol Buttons################
        FociCountVol = wx.BoxSizer( wx.VERTICAL )

        self.FociCount = wx.Button( self, wx.ID_ANY, u"Count Foci", wx.DefaultPosition, wx.DefaultSize, 0 )
        FociCountVol.Add( self.FociCount, 0, wx.ALL, 5 )

        self.FociVol = wx.Button( self, wx.ID_ANY, u"Foci Volume", wx.DefaultPosition, wx.DefaultSize, 0 )
        FociCountVol.Add( self.FociVol, 0, wx.ALL, 5 )
        
        self.BatchProcess = wx.Button( self, wx.ID_ANY, u"Batch Process", wx.DefaultPosition, wx.DefaultSize, 0 )
        FociCountVol.Add( self.BatchProcess, 0, wx.ALL, 5 )
        
        ButtonWrap.Add( FociCountVol, 1, wx.EXPAND, 5 )
        ##################End of Sizer 6 stuffs ######################
        
        ################# Colour buttons#####################
        ColourChoose = wx.BoxSizer( wx.VERTICAL )

        self.GreenBtn = wx.ToggleButton( self, wx.ID_ANY, u"Green", wx.DefaultPosition, wx.DefaultSize, 0 )
        ColourChoose.Add( self.GreenBtn, 0, wx.ALL, 5 )

        self.RedBtn = wx.ToggleButton( self, wx.ID_ANY, u"Red", wx.DefaultPosition, wx.DefaultSize, 0 )
        ColourChoose.Add( self.RedBtn, 0, wx.ALL, 5 )

        self.CalBtn = wx.Button(self, wx.ID_ANY, u"Calibrate", wx.DefaultPosition, wx.DefaultSize,0)
        ColourChoose.Add(self.CalBtn, 0, wx.ALL, 5)
        
        ButtonWrap.Add( ColourChoose, 1, wx.EXPAND, 5 )
        
        ##################End of Colour Button stuffs ######################
        
        wSizer5.Add(ButtonWrap, 1,0,5)
        
        self.outputList = wx.dataview.DataViewListCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(200,400), wx.dataview.DV_SINGLE)
        self.outputList.AppendTextColumn('Foci Count', width=100)  # normal text column
        self.outputList.AppendTextColumn("Foci Vol/Int", width=100)
        self.outputList.SetRowHeight(30)  # define all rows height
        
        wSizer5.Add( self.outputList, 0, wx.ALL, 5 )

        self.contrastSlider = wx.Slider( self, wx.ID_ANY,25, 0, 50, wx.DefaultPosition, wx.Size( 200,-1 ), wx.SL_VERTICAL|wx.SL_AUTOTICKS|wx.SL_MIN_MAX_LABELS)
        wSizer5.Add( self.contrastSlider, 0, wx.ALL, 5 )
        
        self.CircleBtn = wx.ToggleButton(self, wx.ID_ANY, u"Circles On/Off", wx.DefaultPosition, wx.DefaultSize,0)
        self.CircleBtn.SetValue(True)
        wSizer5.Add( self.CircleBtn, 0, wx.ALL, 5 )
        
        self.SaveBtn = wx.Button(self, wx.ID_ANY, u"Save Current Image", wx.DefaultPosition, wx.DefaultSize,0)
        wSizer5.Add( self.SaveBtn, 0, wx.ALL, 5 )
        
        self.NucBtn = wx.Button(self, wx.ID_ANY, u"Check Nucleus", wx.DefaultPosition, wx.DefaultSize,0)
        wSizer5.Add( self.NucBtn, 0, wx.ALL, 5 )
        
        wSizer1.Add(wSizer5, 1,0,5)

        self.SetSizer( wSizer1 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.BatchProcess.Bind(wx.EVT_BUTTON, self.BatchProcessBtnPush)
        self.imSlider.Bind( wx.EVT_SLIDER, self.SlideChange )
        self.contrastSlider.Bind( wx.EVT_SLIDER, self.contrastChange )
        self.LoadFolderBtn.Bind( wx.EVT_BUTTON, self.LoadFolderBtnPush )
        self.LoadFileBtn.Bind( wx.EVT_BUTTON, self.LoadFileBtnPush )
        self.m_listBox1.Bind( wx.EVT_LISTBOX, self.ListBoxItemSelect )
        self.GreenBtn.Bind( wx.EVT_TOGGLEBUTTON, self.GreenBtnPush )
        self.RedBtn.Bind( wx.EVT_TOGGLEBUTTON, self.RedBtnPush )
        self.FociCount.Bind( wx.EVT_BUTTON, self.FociCountBtnPush )
        self.FociVol.Bind( wx.EVT_BUTTON, self.FociVolBtnPush )
        self.CalBtn.Bind(wx.EVT_BUTTON, self.Calibrate)
        self.SaveBtn.Bind(wx.EVT_BUTTON, self.SaveImage)
        self.CircleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.CircleBtnPush)
        self.NucBtn.Bind(wx.EVT_BUTTON, self.NucBtnPush)
        
    def __del__( self ):
        pass

        

    # Virtual event handlers, overide them in your derived class
    def SaveImage(self,event):
        file = filedialog.asksaveasfilename(filetypes=[('PNG','*.png')], defaultextension=[('PNG','*.png')])
        self.testPanel.axes.axis('off')
        self.testPanel.figure.savefig(file,bbox_inches = 'tight')

    def NucBtnPush(self, event):
        global currentData,checkstate
        #Threshold nuc images
        nuc_display = numpy.zeros([sizeZ,sizeY,sizeX])
        nuc_bg      = threshold_yen(blueData)
        def checkNuc(j):
            close_strel = disk(8)
            nuc_img = blueData[j]
            
            if nuc_img.sum() == 0:
                nuc_mask = numpy.zeros([sizeY,sizeX])
            else:
                nuc_thresh = threshold_triangle(nuc_img)
                bw = nuc_img > numpy.max([nuc_thresh,nuc_bg])                
                bw2 = cv2.morphologyEx(numpy.float32(bw),cv2.MORPH_CLOSE,close_strel)
                bw3 = numpy.float32(bw2)
                mask = numpy.zeros((sizeY+2, sizeX+2), numpy.uint8) 
                cv2.floodFill(bw3,mask,(0,0),255)
                cv2.floodFill(bw3,mask,(sizeX-1,sizeY-1),255)
                bw4 = bw3.astype(numpy.uint8)
                nuc_mask = cv2.morphologyEx(cv2.bitwise_not(bw4),cv2.MORPH_OPEN,close_strel) > 0
            return nuc_mask

            
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = executor.map(checkNuc,range(sizeZ))
        y = 0   
        for x in result:
            nuc_display[y,:,:] = x 
            y += 1
        global oriData,fociData
        oriData = blueData
        fociData = nuc_display
        k = round(self.contrastSlider.GetValue())
        self.testPanel.axes.clear()
        self.testPanel.imshow(oriData[currentIndex]+fociData[currentIndex]*k,cmap='inferno')
        
        checkstate = 2

        
        
    def CircleBtnPush(self, event):
        if self.CircleBtn.GetValue() == True:
            self.testPanel.axes.clear()
            drawCircles(self.testPanel.axes,currentCentroid)
            self.testPanel.imshow(currentData)
        elif self.CircleBtn.GetValue() == False:
            self.testPanel.axes.clear()
            self.testPanel.imshow(currentData)

            
    def Calibrate(self, event):
        t1= time.perf_counter()
        thresh_list = []
        fullpath_list = glob.glob(path+'/*czi')
        def cal(path):
            reader = AICSImage(path)
            full_data = reader.data                                       
            # Splitup data into RGB data
            cleanData = splitDataRGB(full_data)
            redData = cleanData[0]
            greenData = cleanData[1]
            blueData = cleanData[2]

            nuc_im = numpy.max(blueData, axis = 0)
            nuc_mask = nuc_im > threshold_triangle(nuc_im)
            print(f'done with {path}')
            return [threshold_otsu(redData * nuc_mask),threshold_yen(greenData * nuc_mask)]
            
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threshs = executor.map(cal,fullpath_list)    
        for result in threshs:
            thresh_list.append(result)
        #returns threshold values for [red,green]
        global calthresh
        calthresh = numpy.average(thresh_list,0)
        print("calibrated!!! Threshold is now {} for red and {} for green".format(calthresh[0],calthresh[1]))
        t2= time.perf_counter()
        print(f'Calibrated in {t2-t1}')
        self.threshR.entry.SetValue(str(round(calthresh[0],2)))
        self.threshG.entry.SetValue(str(round(calthresh[1],2)))

        
    def BatchProcessBtnPush(self, event):
        splitted = path.split('/')
        excel_file_name  = splitted[-2] + '_' + splitted[-1] + '_Output'
        excel_sheet_name = splitted[-2] + splitted[-1]
        test_file_name = filedialog.asksaveasfilename(initialfile = excel_file_name,title='Save Excel Output',filetypes=[('xlsx','*.xlsx')], defaultextension=[('xlsx','*.xlsx')])
        if test_file_name != '':
            excel_file_name = test_file_name.split('.')[0]
        else:
            event.Veto()
        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(columns=['Name','GC','GCPV','RC','RCPV','NucV'], dtype = numpy.float32)
        if self.gVcb.GetValue():
            df.insert(len(df.columns)-3,'GV','')
            df.insert(len(df.columns)-3, 'GVPV', '')
            df.insert(len(df.columns)-3, 'GIPVFB', '')
        if self.gIcb.GetValue():
            df.insert(len(df.columns)-3,'GI','')
            df.insert(len(df.columns)-3, 'GIPV', '')        
        if self.rVcb.GetValue():
            df.insert(len(df.columns)-1,'RV','')
            df.insert(len(df.columns)-1, 'RVPV', '')
            df.insert(len(df.columns)-3, 'RIPVFB', '')
        if self.rIcb.GetValue():
            df.insert(len(df.columns)-1,'RI','')
            df.insert(len(df.columns)-1, 'RIPV', '')        
              
        namelist = []
        fullpath_list = glob.glob(path + '/*.czi')
        for i in fullpath_list:
            namelist.append(i.split('\\')[-1])

        df.Name = namelist
        
        for i in range(len(fullpath_list)):
            global fullpath
            fullpath = fullpath_list[i]
            self.LoadFileBtnPush(event)           
            #Green Count/Vol
            self.FociCountBtnPush(event)
            df.at[i,'GC'] = FociNum          
            self.FociVolBtnPush(event)
            if self.gVcb.GetValue():
                df.at[i,'GV'] = FociVol
                df.at[i,'GVPV'] = FociVolPerVol
                df.at[i,'GCPV'] = FociNum/nuc_vol
                df.at[i,'GIPVFB'] = IntensityVolPerVol
                df.at[i,'NucV'] = nuc_vol
            if self.gIcb.GetValue():
                df.at[i,'GI'] = FociInt
                df.at[i,'GIPV'] = FociIntPerVol
                df.at[i,'GCPV'] = FociNum/nuc_vol
                df.at[i,'NucV'] = nuc_vol
            updateExcel(df,excel_file_name,excel_sheet_name)
            print(f" Finished processing Green image for {namelist[i]}")       
            
            #Change colour
            self.RedBtn.SetValue(True)
            self.GreenBtn.SetValue(False)
            
            #Red Intensity/Vol
            self.FociCountBtnPush(event)
            df.at[i,'RC'] = FociNum            
            self.FociVolBtnPush(event)
            if self.rVcb.GetValue():
                df.at[i,'RV'] = FociVol
                df.at[i,'RVPV'] = FociVolPerVol
                df.at[i,'RCPV'] = FociNum/nuc_vol
                df.at[i,'RIPVFB'] = IntensityVolPerVol
                df.at[i,'NucV'] = nuc_vol
            if self.rIcb.GetValue():
                df.at[i,'RI'] = FociInt
                df.at[i,'RIPV'] = FociIntPerVol
                df.at[i,'RCPV'] = FociNum/nuc_vol
                df.at[i,'NucV'] = nuc_vol

            updateExcel(df,excel_file_name,excel_sheet_name)
            print(f" Finished processing Red image for {namelist[i]}")
            
    def LoadFolderBtnPush( self, event):
         tkroot = tkinter.Tk()
         tkroot.withdraw() #For windows dialog to ask for folder
         global path, file_List #Make path accessible from other functions/callbacks
         path = filedialog.askdirectory()
         file_List = os.listdir(path)
         self.m_listBox1.Set(file_List)
    
    
    def LoadFileBtnPush( self, event ):
        
        #Set greenFoci to be initial interest
        self.GreenBtn.SetValue(True)
        self.RedBtn.SetValue(False)
        #Read CZI file
        #reader = AICSImage(fullpath)
        #full_data=reader.data
        full_data = czifile.imread(fullpath)
        #Metadata collection
        #meta = reader.metadata
        meta = czifile.CziFile(fullpath).metadata()
        root = ET.fromstring(meta)
        global pixelsize_X,pixelsize_Y,pixelsize_Z,sizeX,sizeY,sizeZ,numBit,areaScale
        global redData,greenData,blueData, currentIndex, currentData,checkstate #make data global,accessible from other callbacks
        pixelsize_X = float(root.findall('.//ScalingX')[0].text)
        pixelsize_Y = float(root.findall('.//ScalingY')[0].text)

        areaScale = pixelsize_X*pixelsize_Y 
        sizeX = int(root.findall('.//SizeX')[0].text)
        sizeY = int(root.findall('.//SizeY')[0].text)
        numBit = root.findall('.//PixelType')[0].text
        
        if full_data.shape[4] != 1:
            sizeZ = int(root.findall('.//SizeZ')[0].text)
            pixelsize_Z = float(root.findall('.//ScalingZ')[0].text)
            currentIndex = round(sizeZ/2)
        else:
            sizeZ = 1
            currentIndex = 0
        # Splitup data into RGB data

        cleanData = splitDataRGB(full_data)
        redData = cleanData[0]
        greenData = cleanData[1]
        blueData = cleanData[2]
        

        currentData = blueData
        dataTest = currentData[currentIndex]        

        
        #Show image on axes
        self.testPanel.axes.clear()

        self.testPanel.imshow(dataTest)
        self.imSlider.SetRange(1,sizeZ)
        self.imSlider.SetValue(currentIndex)
        
        checkstate = 1
        
        #Finish Loading
        #self.LoadingBar.SetValue(100)
        #self.LoadingBar.SetDrawValue(draw=True, drawPercent=True, font=None, colour=wx.BLACK, formatString='Loaded!')
        
    def ListBoxItemSelect( self, event ):
        file_name = self.m_listBox1.GetString(self.m_listBox1.GetSelection())
        global fullpath
        fullpath = "{}/{}".format(path,file_name)

    def GreenBtnPush( self, event ):
        self.RedBtn.SetValue(False)

    def RedBtnPush( self, event ):
        self.GreenBtn.SetValue(False)    
        
    def FociCountBtnPush( self, event ):
        
        global nuc_area,FociNum,FociNumPerArea,currentData,currentCentroid
        nuc_im = numpy.max(blueData, axis = 0)
        nuc_mask = nuc_im > threshold_triangle(nuc_im)
        nuc_area = nuc_mask.sum() * areaScale * 10**12 #um^2
        
        if self.GreenBtn.GetValue() == True:
            data    = greenData
            thresh  = numpy.float(self.threshG.entry.GetValue())
        elif self.RedBtn.GetValue() == True:
            data    = redData
            thresh  = numpy.float(self.threshR.entry.GetValue())
        minFociSize     = int(self.minFociSize.entry.GetValue())
        maxFociSize     = int(self.maxFociSize.entry.GetValue())
        tophat_strel    =  disk(maxFociSize) #Structuring elements
        open_strel      = disk(minFociSize)
        sum_img         = numpy.max(data, axis = 0)  #Maximum Intensity Projection, get rid of bg
        final_sum       = sum_img * nuc_mask
        
        if numpy.sum(final_sum) == 0:
            label_img = final_sum
            centroidData = []; areaData = 0;
        else:
            im_tophat = cv2.morphologyEx(final_sum,cv2.MORPH_TOPHAT,tophat_strel) #Tophat for uneven lighting/get rid of large obj
            th = threshold_yen(im_tophat)
            bw_img = im_tophat > numpy.max([thresh,th])
            bw_img2 = cv2.morphologyEx(numpy.float32(bw_img),cv2.MORPH_OPEN,open_strel)
            
            centroidData=[]; areaData =[]
            label_img = skimage.measure.label(bw_img2)
            centroidData, areaData = getCentroidArea_Data(label_img)
    
        #Show Data
        self.testPanel.axes.clear()
        drawCircles(self.testPanel.axes,centroidData)
        self.CircleBtn.SetValue(True)
        self.testPanel.imshow(sum_img)
        currentCentroid = centroidData
        currentData = sum_img
        
        FociNum         = numpy.amax(label_img)
        FociNumPerArea  = FociNum/nuc_area
        self.outputList.AppendItem([str(FociNum),''])
        #print('Foci num per um^2 is ' + '{}'.format(FociNumPerArea))

    def FociVolBtnPush( self, event ):

        global nuc_vol,checkstate
        if self.GreenBtn.GetValue() == True:
            data = greenData
            volChecked = self.gVcb.GetValue()
            intChecked = self.gIcb.GetValue()
        elif self.RedBtn.GetValue() == True:
            data = redData
            volChecked = self.rVcb.GetValue()
            intChecked = self.rIcb.GetValue()
       
        minFociSize = int(self.minFociSize.entry.GetValue())/2 #By default take half to account for varying size along z axis
        maxFociSize = int(self.maxFociSize.entry.GetValue())
        sum_nuc = numpy.amax(blueData,axis=0)
        pre_nuc_mask = numpy.zeros(data.shape, dtype=bool)
        pre_nuc_mask[:,:,:] = sum_nuc[numpy.newaxis,:,:] > threshold_triangle(sum_nuc)
        

        volumeData  = data * pre_nuc_mask
        nuc_bg      = threshold_yen(blueData)
        foci_bg     = threshold_otsu(volumeData)
        nuc_vol     = 0
        intSum      = 0
        areaSum     = 0
        def getFociVol(j):
            ### Nucleus stuff ###
            close_strel = disk(8)
            nuc_img = blueData[j]
            if nuc_img.sum() == 0:
                nuc_vol_slice = 0
                nuc_mask = numpy.zeros([sizeX,sizeY])
            else:
                nuc_thresh = threshold_triangle(nuc_img)
                bw = nuc_img > numpy.max([nuc_thresh,nuc_bg])                
                bw2 = cv2.morphologyEx(numpy.float32(bw),cv2.MORPH_CLOSE,close_strel)
                bw3 = numpy.float32(bw2)
                mask = numpy.zeros((sizeY+2, sizeX+2), numpy.uint8) 
                cv2.floodFill(bw3,mask,(0,0),255)
                cv2.floodFill(bw3,mask,(sizeX-1,sizeY-1),255)
                bw4 = bw3.astype(numpy.uint8)
                nuc_mask = cv2.morphologyEx(cv2.bitwise_not(bw4),cv2.MORPH_OPEN,close_strel) > 0
                nuc_area = nuc_mask.sum() * pixelsize_X * pixelsize_Y
                nuc_vol_slice = nuc_area * pixelsize_Z * 10**18 #Convert to um^3    
                #####################
            
            tophat_strel = disk(maxFociSize)
            open_strel = disk(minFociSize)                # Volume use size 2? Foci smaller size as it gets out of focus plane
            adj_img = volumeData[j] * nuc_mask  #Remove stray pixels outside of nucleus
            RGBImage = numpy.zeros([sizeX,sizeY,3],dtype=numpy.uint8)
            
            im_tophat = cv2.morphologyEx(adj_img,cv2.MORPH_TOPHAT,tophat_strel)
            th = threshold_yen(im_tophat)
            bw_img = im_tophat > numpy.max([foci_bg,th])
            bw_img2 = cv2.morphologyEx(numpy.float32(bw_img),cv2.MORPH_CLOSE,open_strel)
            bw_img3 = cv2.morphologyEx(numpy.float32(bw_img2),cv2.MORPH_OPEN,open_strel)
            areaData = bw_img3.sum()
            intensity = (bw_img3*adj_img).sum()
            ori_img = cv2.normalize(adj_img, None,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
            foci_img = bw_img3
            return areaData,nuc_vol_slice,ori_img,foci_img,intensity
        
        def getFociIntensity(j):
         ############### Nucleus stuff ###################
            close_strel     = disk(8)
            nuc_img         = blueData[j]
            if nuc_img.sum() == 0:
                nuc_mask        = numpy.zeros([sizeX,sizeY])
                nuc_vol_slice   = 0
            else:
                nuc_thresh      = threshold_triangle(nuc_img)
                bw              = nuc_img > numpy.max([nuc_thresh,nuc_bg])                
                bw2             = cv2.morphologyEx(numpy.float32(bw),cv2.MORPH_CLOSE,close_strel)
                bw3             = numpy.float32(bw2)
                mask            = numpy.zeros((sizeY+2, sizeX+2), numpy.uint8) 
                
                cv2.floodFill(bw3,mask,(0,0),255)
                cv2.floodFill(bw3,mask,(sizeX-1,sizeY-1),255)
                
                bw4             = bw3.astype(numpy.uint8)
                nuc_mask        = cv2.morphologyEx(cv2.bitwise_not(bw4),cv2.MORPH_OPEN,close_strel) > 0
                nuc_area        = nuc_mask.sum() * pixelsize_X * pixelsize_Y
                nuc_vol_slice   = nuc_area * pixelsize_Z * 10**18                   #Convert to um^3    
        ###################################################
            
            adj_img = volumeData[j] * nuc_mask                                  #Remove stray pixels outside of nucleus
            intData = adj_img.sum()
            return intData,nuc_vol_slice
        
        ################### Get intensities ##################################
        if intChecked:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = executor.map(getFociIntensity,range(sizeZ))
                
            for (x,y) in result:
                intSum  += x 
                nuc_vol += y        
                
            voxelSize = pixelsize_X*pixelsize_Y*pixelsize_Z
            global FociInt, currentData, FociIntPerVol
    
            FociInt         = intSum       
            FociIntPerVol   = FociInt/nuc_vol
        
            self.outputList.AppendItem(['',str(round(FociIntPerVol,2))])
        
        ################## Get foci vol ######################################
        if volChecked:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = executor.map(getFociVol,range(sizeZ))
            global oriData, fociData, FociVol, FociVolPerVol,IntensityVol,IntensityVolPerVol
            oriData = []; fociData = []; IntensityVol = 0
            for (x,y,j,k,l) in result:
                areaSum += x
                nuc_vol += y
                IntensityVol += l
                oriData.append(j)
                fociData.append(k)

            voxelSize = pixelsize_X*pixelsize_Y*pixelsize_Z

            IntensityVolPerVol = IntensityVol/nuc_vol
            FociVol = areaSum *voxelSize *10**18 #Convert to um^3        
            FociVolPerVol = FociVol/nuc_vol
            self.outputList.AppendItem(['',str(round(FociVolPerVol,2))])
            self.testPanel.axes.clear()
            k = self.contrastSlider.GetValue()
            currentIndex = round(self.imSlider.GetValue())
            self.testPanel.imshow(oriData[currentIndex]+fociData[currentIndex]*k,cmap='inferno')
            #self.testPanel.imshow(currentData[round(sizeZ/2)])
            print('Foci vol per um^3 is ' + '{}'.format(FociVolPerVol))
            print('Intensity vol per um^3 is ' + '{}'.format(IntensityVolPerVol))
            
        checkstate = 2
        
    def SlideChange(self, event):
        k = round(self.contrastSlider.GetValue())
        currentIndex = round(self.imSlider.GetValue())
        if checkstate == 1:
            self.testPanel.axes.clear()
            self.testPanel.imshow(currentData[currentIndex])
        elif checkstate == 2:
            self.testPanel.axes.clear()
            self.testPanel.imshow(oriData[currentIndex]+fociData[currentIndex]*k/10*numpy.amax(oriData[currentIndex]),cmap='inferno')
#        elif checkstate == 3:
#            self.testPanel.axes.clear()
#            self.testPanel.imshow(oriData[currentIndex]+fociData[currentIndex]*10*k,cmap='inferno')
        else:
            pass
        
    def contrastChange(self, event):
        k = round(self.contrastSlider.GetValue())
        currentIndex = round(self.imSlider.GetValue())
        if checkstate == 2:
            self.testPanel.axes.clear()
            self.testPanel.imshow(oriData[currentIndex]+fociData[currentIndex]*k/10*numpy.amax(oriData[currentIndex]),cmap='inferno')
#        elif checkstate == 3:
#            self.testPanel.axes.clear()
#            self.testPanel.imshow(oriData[currentIndex]+fociData[currentIndex]*10*k,cmap='inferno')
        else:
            pass
        
if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    frm = MainFrame(None)
    frm.Show()
    app.MainLoop()