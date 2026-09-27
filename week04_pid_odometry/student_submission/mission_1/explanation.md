# mission_1 Submission

- Name: Ishraq Chowdhury
- Section: CSCI 39536

## Explanations

### prediction

With too little Kp, I expect the arm to slowly reach the target while  with too little KD, I expect  the arm to not reach the target

### tuning_analysis

I predicted that low Kp would make the arm move slowly and low Kd would keep it from reaching the target. I adjusted Kp, Ki, and Kd on both the shoulder and elbow through trial and error until the arm successfully held three target poses. My final settings were Kp = 6.0, Ki = 0.9, and Kd = 1.3 for both joints. I learned that low Kd can cause overshooting and oscillation rather than stopping short. I did not separately test gravity compensation, so I cannot say how much it affected my result.