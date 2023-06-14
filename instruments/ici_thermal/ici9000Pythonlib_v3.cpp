#include "ICIFrameGrabber.h"

#include <iostream>
#include <fstream>
#include <string>

using namespace std;

USBHandler *pUSBHandler = NULL;
float *pRadiometricImage;
ICIFrameGrabber *pFrameGrabber = NULL;

extern "C"
{
	int startCam();
	int loadCal(const char folder_path[]);
	int doNUC();
	void stopCam();
    void getImage(float pRadiometricImage[]);
	void saveImage(const char path[]);
	void getErr(int err);
	void getRaw(const char path[]);
	int getWidth();
	int getHeight();
	int getSize();
	long getSN();
}

int getWidth() {
	int width = pFrameGrabber->GetWidth();
	return width;
}

int getHeight() {
	return pFrameGrabber->GetHeight();
}

int getSize() {
	return (pFrameGrabber->GetWidth() * pFrameGrabber->GetHeight());
}

long getSN() {
	return pFrameGrabber->GetCameraSerialNumber();
}

void getErr(int err) {
	printf("nRtnError = %d, %s\n", err, pFrameGrabber->GetError(err));
}

int startCam()
{
	/*
	if(NULL!= pFrameGrabber)
	{
		return;
	}
	
	if(NULL != pUSBHandler)
	{
		return;
	}
	*/
	std::cout << "SDK Version = " << ICIFrameGrabber::GetVersion() << "\n";
	ICICameraFinder iciCameraFinder;
	std::vector<ICIFrameGrabber *> connectedICICameras;
	
	iciCameraFinder.GetConnectedCameras( connectedICICameras );
	int const nTotalNumberOfICICamerasConnected = connectedICICameras.size();
	std::cout << "Total number of ICI Cameras Connected = " << nTotalNumberOfICICamerasConnected << "\n";
	
	if ( 0 == nTotalNumberOfICICamerasConnected )
	{
		std::cout << "Error. No Cameras found...trying again\n";
		iciCameraFinder.GetConnectedCameras( connectedICICameras );
		int const nTotalNumberOfICICamerasConnected = connectedICICameras.size();
		std::cout << "Total number of ICI Cameras Connected = " << nTotalNumberOfICICamerasConnected << "\n";
		if ( 0 == nTotalNumberOfICICamerasConnected )
		{
			std::cout << "Error. Still no Cameras found...Exiting\n";
			return -1;
		}
	}
	
	pFrameGrabber = connectedICICameras.at(0);
	
	pUSBHandler = pFrameGrabber->StartCamera();
	printf("Camera Started\n");
	printf("Camera Serial Number %ld\n", pFrameGrabber->GetCameraSerialNumber());
	printf("Camera Width = %d\n",pFrameGrabber->GetWidth());
	printf("Camera Height = %d\n",pFrameGrabber->GetHeight());

	return 0;
}

int loadCal(const char folder_path[])
{
	/*
	if(NULL == pFrameGrabber)
	{
		return;
	}
	if(NULL == pUSBHandler)
	{
		return;
	} */
	int nRtnError = pFrameGrabber->LoadCalibrationFile(folder_path);
	printf("nRtnError = %d, %s\n", nRtnError, pFrameGrabber->GetError(nRtnError));
	return nRtnError;

}

int doNUC(){
	int nRtnError = pFrameGrabber->PerformNUC();
	printf("nRtnError = %d, %s\n", nRtnError, pFrameGrabber->GetError(nRtnError));
	return nRtnError;
}

void getImage(float pRadiometricImage[])

{
	/*
    if(NULL == pFrameGrabber)
	{
		return;
	}
	if(NULL == pUSBHandler)
	{
		return;
	} */
    //int nWidth =  pFrameGrabber->GetWidth();
    //int nHeight = pFrameGrabber->GetHeight();
    //pRadiometricImage = new float [nWidth*nHeight];
    int nRtnError = pFrameGrabber->GetTemperatureImage(pRadiometricImage);
	//std::cout << "nRtnError = " + nRtnError + ", " + pFrameGrabber->GetError(nRtnError);
	printf("nRtnError = %d, %s\n", nRtnError, pFrameGrabber->GetError(nRtnError));
}

//Get Image data and save to file
void saveImage(const char path[])
{	/*
    if(NULL == pFrameGrabber)
	{
		return;
	}
	if(NULL == pUSBHandler)
	{
		return;
	} */
	int nWidth =  pFrameGrabber->GetWidth();
    int nHeight = pFrameGrabber->GetHeight();
    float *pRadiometricImage;
    pRadiometricImage = new float[nWidth*nHeight];   
    int nRtnError = pFrameGrabber->GetTemperatureImage(pRadiometricImage);
    if(nRtnError <= 0)
	{	
	    float fMin = -1.0f;
	    float fMax = -1.0f;	
	
	    int i=0;
	    float fCurPixelValue=0;
	
	    
	    for(i=0;i<nWidth*nHeight;i++)
	    {
		fCurPixelValue = pRadiometricImage[i];
		
	        if(fCurPixelValue > fMax)
		{
	            fMax = fCurPixelValue;
		}
	        
	        if(fCurPixelValue < fMin)
	            fMin = fCurPixelValue;
	    }        
	
	    float span = fMax -fMin;
	    if(span==0.0f)
	    { 
	            span = 1.0f;
	    }
	
	    float multconst = 256.0f/span;
	
	    ofstream myfile;
	    myfile.open(path);
	    for(int i=0;i<nWidth*nHeight;i++)
	    {
	        /*float temp = pRadiometricImage[i];
	        int val;
	        val = (int)((temp-fMin)*multconst);
	        if(val>255)
	        {
	                val = 255;
	        }
	        else if(val<0)
	        {
	                val = 0;
	        }*/
	        myfile << pRadiometricImage[i];	
			myfile << ',';
			if ((i+1) % nWidth == 0) myfile << endl;			
	    }
	
	    myfile.close();
	}
    else
	{
	printf("nRtnError = %d, %s\n", nRtnError, pFrameGrabber->GetError(nRtnError));
	}
}

void stopCam()
{
	printf("Stopping camera\n");
	pFrameGrabber->ShutdownCamera();
	delete pFrameGrabber;
}