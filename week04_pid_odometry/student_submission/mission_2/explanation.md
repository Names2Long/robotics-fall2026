# mission_2 Submission

- Name: Ishraq Chowdhury
- Section: CSCI 39536

## Explanations

### prediction

I assume the forwad distance will underestimate its distance and go too forward. While the sideways distance will barley turn

### calibration_analysis

I predicted that the forward estimate would be too low and the robot would barely turn sideways. I learned that strafing means moving sideways without turning. I tuned the forward scale to 0.0494 inches per tick and the strafe scale to 0.0502 inches per tick. These control how encoder ticks become estimated forward and sideways distances. The sideways pod is necessary because the forward pod cannot measure sideways motion. The test passed with a maximum error of 0.80 inches and a final error of 0.37 inches, both below 3 inches. Some drift can remain because of wheel slip, sensor resolution, and small calibration errors that accumulate over time.