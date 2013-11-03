nta_car
=======

Example NuPIC anomaly model to control a toy car via Raspberry Pi

The drive.py file reads the values of two photo sensors and feeds that data into the CLA model.  The car's stearing is hard wired to be light seeking.  There is no training data needed and the car is always learning. The anomaly detection of the model is used to control the car's forward motion.  When the anomaly score is above the threshold, the car will stop to continue learning the current light settings.  Once it has learned the current environment, the anomaly score will drop and the car will start to drive again.


Credits

The NuPIC model code is based on the hotgym example at:
https://github.com/numenta/nupic
