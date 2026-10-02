# PLAN


* ~Docker~:
    * ~setup docker container~
        * ~MTU / PLC field device~
        * ~modbus communication~

* ~Shamir encoding~
    * ~createint i = 0; i < DMA_CHANNEL_COUNT;; i++ key~
    * ~create polynomial and hide key~
    * ~key reconstruction~
    * ~distribute key~
    * ~sign message~
    * ~request keys~


* Evaluation
    * Python time package to time how long verification takes?
        * ~add time for key reconstruction and instruction signing~
        * show field device register value changing
        * add timings for each section
        * add control variable (no SSS used) - time taken for raw instructions 
