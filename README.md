# SCADA-Shamir-Secrets

<p align="center">
    <img src="https://github.com/henrylewis2004/SCADA-Shamir-Secrets/blob/main/.github/images/shamirs.png" width = "400"/>
</p>

## Plan

MTU -----------------------------> PLC --------------> does something

(sends command) ----> (authorises command) ----> does something


|Component|Method|Implemented|
|---|---|---|
|System Simulation|Docker|X|
|MTU|Node-Red Docker Container|X|
|PLC|Python Docker Container|X|
|Shamir|Python Script|X|


### Steps
-- MTU instruction --
1. MTU wants to send command
2. MTU requests shares from field devices
3. MTU reconstructs key
4. MTU signs instruction
5. MTU sends instruction to relevant PLC
6. PLC verifies instruction (how?)
7. PLC performs instruction
   
-- PLC Communication --
   
8. PLC sends information back to MTU
9. MTU verifies information signature
