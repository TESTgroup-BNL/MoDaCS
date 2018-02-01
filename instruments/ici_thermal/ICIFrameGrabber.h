#ifndef FRAMEGRABBER_H
#define FRAMEGRABBER_H
#include "libusb-1.0/libusb.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>


enum RTNERRORS 
{
	NO_ERROR = 0,
	NULL_USB_HANDLER,
	NULL_IMAGE_DATA,
        NULL_FPA_LENS_DATA,
	NULL_FILE_POINTER,
	BAD_WIDTH,
        BAD_HEIGHT,
	RECEIVED_SHORT_FRAME,
	ERROR_SERIAL_NUMBER,
	CAL_FILE_NOT_FOUND,
        CAL_FILE_NOT_LOADED,
        ERROR_IN_LOADING_CALIBRATION_FILE,
        ERROR_IN_LOADING_AUTONUC_FILE,
        AUTO_NUC_FILE_NOT_FOUND,
        OUT_OF_MEMORY_ERROR,
        PATH_NOT_EXISIS
};



#define PRINTFS

#ifdef PRINTFS
#define VDBG(...) do {\
			printf(__VA_ARGS__);\
			FILE *fp = fopen("log.txt","at");fprintf(fp,__VA_ARGS__);fclose(fp);\
			}while(0)
#else
#define VDBG(...)
#endif




class USBHandler
{
public:
	struct libusb_device_handle *m_USBHandle;
	libusb_context *m_Context;
};

class ICIFrameGrabber
{
private:
	int m_nWidth, m_nHeight;
	long m_CameraSerialNumber;
	unsigned short m_nFPA;
	float m_nLens;
        
public:
    
	ICIFrameGrabber();

	/*
	 * Description: StartCamera will start the camera and establish connection with the camera. 
	 *
	 * Return value:
	 * On Success, StartCamera return the pointer to the USBHandler class.
	 */
	USBHandler *StartCamera();

	/*
	 * Description: ShutdownCamera will disconnect the camera from the host application. 
	 *
	 * Arguments:
	 * USBHandler *pUSBHandler: Pointer to the USBHandler class. 
	 *
	 */

	void ShutdownCamera(USBHandler *pUSBHandler);

	/*
	 * Description: GetCameraSerialNumber returns the camera serial number. User need to call StartCamera before calling this method.
	 *
	 * Return Value:
	 * GetCameraSerial returns ERROR_SERIAL_NUMBER on failure. 
	 */

	long GetCameraSerialNumber();

	/*
	 * Description: GetWidth returns the width of the image. User need to call StartCamera before calling this method. 
	 *
	 * Return Values:
	 * GetWidth returns BAD_WIDTH_HEIGHT on failure. 
	 */
	int GetWidth();

	/*
	 * Description: GetHeight returns the height of the image. User need to call StartCamera before calling this method. 
	 *
	 * Return Value:
	 * GetHeight returns BAD_WIDTH_HEIGHT on Failure. 
	 */
	int GetHeight();

	/*
	 * Description: Receive FPA and Lens temperature values from the camera that requires for the calibrated data.
	 * 
	 * Arguments:
	 * USBHandler *pUSBHandler: Pointer to the USBHandler class. Pointer to the USBHandler class can be received by calling the StartCamera() method.
	 * unsigned char *pFPALens: User need to allocate 26 bytes to receive pFPALensData. 
	 * 
	 * Return Value:
	 * GetFPALens returns one of the values from RTNERRORS. On Success, GetFPALens returns NO_ERROR.
	 *
	 */
	int GetFPALens(USBHandler *pUSBHandler,unsigned char *pFPALensData);

	/* Description: Receive FPA and Lens temperature values from the camera that requires for the calibrated data.
	 * 
	 * Arguments:
	 * USBHandler *pUSBHandler: Pointer to the USBHandler class. Pointer to the USBHandler class can be received by calling the StartCamera() method.
	 * unsigned short *fpa: Unsigned short variable to store fpa value.
	 * float *fpa: float variable to store lens value. 
	 * 
	 * Return Value:
	 * GetFPALens returns one of the values from RTNERRORS. On Success, GetFPALens returns NO_ERROR.
	 *
	 */
	int GetFPALens(USBHandler *pUSBHandler,float *fpa, float *lens,unsigned short *fpaState);


	/*
	 * Description: GetImageData get single frame from the camera.
	 * 
	 * Arguments:
	 * USBHandler *pUSBHandler: Pointer to the USBHandler class. Pointer to the USBHandler class can be received by calling the StartCamera() method.
	 * unsigned short *pImageData: Pointer of unsigned short to receive the frame data. User would need allocate the memory for pImageData. 
	 * 			       User should allocate width*height*sizeof(unsigned short) memory for pImageData.
	 * int *transferred: Transferred returns the number of bytes received from the camera.
	 *
	 * Return Value:
	 * GetImageData returns one of the values from RTNERRORS. On Success, GetImageData returns NO_ERROR.
	 *
	 */
	int GetImageData(USBHandler *pUSBHandler,unsigned short *pImageData,int *transferred);

	/*
	 * Description: ControlShutter will either open or close the shutter. 
	 *
	 * Arguments: 
	 * USBHandler *pUSBHandler: Pointer to the USBHandler class. Pointer to the USBHandler class can be received by calling the StartCamera() method. 
	 * bool bOpen: true to open the shutter, false to close the shutter.
	 *
	 * Return Value:
	 * ControlShutter returns one of the values from RTNERRORS. On Success, ControlShutter returns NO_ERROR.
	 */

	 int ControlShutter(USBHandler *pUSBHandler, bool bOpen);	

	/*
	 * Description: PerformNUC will do non uniformity correction. 
	 *
	 * Arguments: 
	 * USBHandler *pUSBHandler: Pointer to the USBHandler class. Pointer to the USBHandler class can be received by calling the StartCamera() method. 
	 *
	 * Return Value:
	 * PerformNUC returns one of the values from RTNERRORS. On Success, PerformNUC returns NO_ERROR.
	 */
	 int PerformNUC(USBHandler *pUSBHandler);

	 /*
	  * Description: SaveX16Image that can be loaded in Windows using IR Flash software.
	  *
	  * Arguments
	  * USBHanlder *pUSBHandler: Pointer to the USBHandler class.
	  * const char *path: FullPath to store the file. 
	  */
	 int SaveX16Image(USBHandler *pUSBHandler,const char *path);
	 
	 /*
	  * Description: SaveX16Image that can be loaded in Windows using IR Flash software.
	  *
	  * Arguments
	  * USBHanlder *pUSBHandler: Pointer to the USBHandler class.
	  * FILE *pFP: pointer to the FILE. User need to make sure to pass the open file pointer and need to close the file pointer.  
	  */
	 int SaveX16Image(USBHandler *pUSBHandler, FILE *pFP);
         
         /*
          * Description: GetRadiometricImage will get the raw Image from the Camera, Convert to Radiometric Data and store the data in the pRadiometricImage
          * buffer. User have to allocate the memory for the radiometric Image. User should allocate memory to CameraResolution(Width*Height)*sizeof(float). 
          * Also, user need to call the LoadCalibrationFile method once before calling this method. 
          * 
          * Arguments
          * USBHandler *pUSBHandler: Pointer to the USBHandler class.
          * float *pRadiometricImage: Pointer of float that store the radiometric data. 
          * 
          * Return Value:
	  * GetRadiometricImage returns one of the values from RTNERRORS. On Success, GetRadiometricImage returns NO_ERROR.
          */
         int GetRadiometricImage(USBHandler *pUSBHandler, float *pRadiometricImage);
          
         /*
          * Description: LoadCalibrationFile load the calibration file of the camera. Calibration File is necessary to convert Raw 14 data to radiometric
          * data. Calibration Files should be of Cal<CameraSerialNumber>F.bin.
          * 
          * Arguments:
          * USBHandler *pUSBHandler: Pointer to the USBHandler class.
          * const char *path: Path of the folder that contains the calibration file. 
          * 
          * Return Value:
	  * LoadCalibrationFile returns one of the values from RTNERRORS. On Success, LoadCalibrationFile returns NO_ERROR.
          */
         int LoadCalibrationFile(USBHandler *pUSBHandler,const char *path);
         
         
         /*
          * GetError will return the error code in string format. 
          */
         const char *GetError(int nEnumVal);
};


#endif
