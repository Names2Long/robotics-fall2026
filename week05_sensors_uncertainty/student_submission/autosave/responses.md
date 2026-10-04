# Week 5: Sensors, Noise, and Uncertainty

- name: Ishraq Chowdhury
- email: ASIL.CHOWDHURY41@stu-mail.hunter.cuny.edu
- course_id: CSCI 39536

## concepts.observation

I noticed that the noise changes the spread of the data while the bias changes the median of the data 

## final.course_reflection

This lab went more smoothly for me compared to the previous labs, and I did not have many major issues. The only main hiccup I had was in Mission 3, when I thought I had saved and tested my changes, but the checklist still showed missing requirements or added upon missing requirements. I wasn’t t sure whether a response had failed to save or whether my settings no longer matched the recorded test. That experience reminded me to check that my results were recorded before moving on.

What stood out was that making sensor readings smoother did not always improve the overall result. Increasing the averaging window could increase error, and different sensor weights affected response time. Seeing those tradeoffs in the results helped make the concepts more concrete.

The warehouse and assistive scenarios also showed why technical choices need to consider people. An unsafe decision could put someone at risk, while repeated unnecessary stops could interrupt their work or independence. Overall this helped me see robotics as more than getting code to run. Since it also involves testing whether the system’s behavior makes sense for the people near it and the people designing it.

## final.synthesis

This lab showed how sensor imperfections affect estimation and robot decisions. In Mission 1, my sensor had a mean of 1.9859 m and a bias of −0.0141 m, with sample variance of 0.004307 m^2. Most readings were 2.00 or 1.90 m, indicating coarse resolution. There were six dropouts and one outlier. More samples wouldn’t remove the limited resolution of individual readings.

In Mission 2, increasing the moving average window from 3 to 11 increased RMSE from 0.1395 to 0.1601 m, while measured response delay remained 1.10 s. More smoothing therefore did not guarantee better overall accuracy. I selected median filtering with window 3 and equal sensor weights because it achieved the lowest recorded RMSE, 0.1270 m, with a 0.90 s delay and 100% availability. However, availability included held estimates rather than exclusively fresh measurements.

Mission 3 connected these estimates to consequences for people. Recorded warehouse revisions reduced maximum detection delay from 0.10 to 0.00 s, but the false safe rate remained 0.6173%. Assistive revisions reduced delay from 0.05 to 0.00 s while maintaining a zero false safe rate. These results show why policies must balance unsafe movement against unnecessary interruptions. Seven simulated scenarios provide useful comparative evidence, but zero dangerous command events do not prove physical safety. Deployment would require stakeholder input and testing of real stopping distances, sensor failures, and operating conditions.

## mission_1.bias

-0.0141

## mission_1.bias_vs_variance

My prediction distinguished a shift in the mean from the scattered readings. The measured mean is 1.9859 m, giving a small negative bias of −0.0141 m, while the sample variance is 0.004307 m². Bias measures how far the mean is from the true distance, while variance measures how spread out the readings are. Most readings are exactly 2.00 m or 1.90 m, suggesting coarse resolution rather than a systematic bias. The 1.10 m outlier also increases the variance.

## mission_1.dropouts

6

## mission_1.mean

1.9859

## mission_1.median

2.0000

## mission_1.more_samples

More samples would not remove the sensors coarse resolution. Out of the 234 valid readings, 209 are 2.00 m and 24 are 1.90 m, showing that measurements fall on discrete levels. More samples could make the estimated mean more stable, but that would not make individual readings more precise. The small bias of −0.0141 m does not mean the sensor can reliably distinguish distances between those levels.

## mission_1.outliers

1

## mission_1.prediction

I predict that a consistently biased sensor could produce readings around 2.20 m. Its mean would be above the distance of 2.00 m, giving a bias of about +0.20 m. Its variance would be low because the readings are too close together.

A noisy sensor without systematic bias would produce more scattered readings. Its mean should be close to 2.00 m and its bias close to zero, but its variance would be higher because the readings are more spread out

## mission_1.prediction_draft

I predict that a consistently biased sensor could produce readings around 2.20 m. Its mean would be above the distance of 2.00 m, giving a bias of about +0.20 m. Its variance would be low because the readings are too close together.

A noisy sensor without systematic bias would produce more scattered readings. Its mean should be close to 2.00 m and its bias close to zero, but its variance would be higher because the readings are more spread out

## mission_1.profile

quantized

## mission_1.robot_consequence

An assistive robot might stop when its measured distance from a person falls below 1.95 m. With coarse resolution, a distance just below that threshold could round to 2.00 m, causing the robot to continue moving when it should stop. This could make the person feel unsafe or increase the risk of contact. The stopping policy should account for the sensors limited resolution

## mission_1.variance

0.004307

## mission_2.comparison

At a fixed Sensor A weight of 0.25, moving average windows 3, 7, and 11 produced RMSE values of 0.1395, 0.1504, and 0.1601 m. Compared with window 3, RMSE increased by 0.0109 m for window 7 and 0.0205 m for window 11. All three had the same measured response delay of 1.10 s. For the matched window 3 comparison, median filtering slightly reduced RMSE from 0.1395 to 0.1389 m, while delay remained 1.10 s. However, maximum error increased from 1.1254 to 1.2746 m, so the median did not improve every metric.

## mission_2.fusion_choice

Using median window 3 with other settings fixed, Sensor A weights of 0.25, 0.50, and 0.75 produced RMSE values of 0.1389, 0.1270, and 0.1335 m, with delays of 1.10, 0.90, and 0.45 s. Maximum errors were 1.2746, 1.4397, and 1.6049 m, respectively. I selected weight 0.50 because it gave the lowest RMSE while meeting every required limit. Compared with weight 0.25, it reduced RMSE by 0.0119 m and delay by 0.20 s. Weight 0.75 responded faster, but increased RMSE and maximum error. Sensor A is fast but noisy and prone to outliers, while Sensor B is steadier but biased and slower. Equal weighting provided a useful balance in my recorded tests.

## mission_2.manual_average

4.1667

## mission_2.manual_fusion

2.25

## mission_2.manual_median

2.3

## mission_2.prediction_draft

Compared with median window 3 at weight 0.50, increasing Sensor A’s weight to 0.75 may improve responsiveness further, but remaining noise and outliers from Sensor A could increase error.

## mission_2.responsiveness

Smoothing combines recent readings to reduce fluctuations, but older readings can slow the response to a real change. In my experiments, increasing the moving average window from 3 to 7 to 11 did not change the measured sustained response delay. They all were 1.10 s. This did not support my prediction of increasing delay for these settings. With median window 3, increasing Sensor A’s weight from 0.25 to 0.50 to 0.75 reduced delay from 1.10 to 0.90 to 0.45 s. My selected configuration took 0.90 s to achieve three consecutive estimates within 0.15 m of the new truth. If a person moved closer, delayed distance estimates could postpone a robot’s stopping decision. Also, 100% availability includes held estimates and does not guarantee fresh evidence.

## mission_2.selected

6

## mission_3.Assistive.prediction_draft

Testing / debugging purposes since its not letting me continue even though I did all the necessary tests 

## mission_3.Warehouse.prediction_draft

Compared with my previous weight only test, I predict that increasing the caution margin by 0.10 m will encourage earlier stops and may reduce false safe decisions. The tradeoff could be more unnecessary stops, delaying workers and deliveries.

## mission_3.context_comparison

My final warehouse policy uses a stopping threshold of 0.75 m and margin of 0.20 m, giving a stop boundary of 0.95 m. My assistive policy uses a threshold of 0.95 m and margin of 0.25 m, giving a larger stop boundary of 1.20 m. This provides more distance before stopping near someone who may have difficulty moving away. Sensor A’s weight also differs, 0.50 for warehouse and 0.35 for assistive. The assistive policy relies more on steadier Sensor B, although its bias and slower updates remain limitations. Both policies recorded 0.00 s maximum detection delay and zero dangerous command events. Warehouse false safe and stop rates were 0.6173% and 5.6122%, compared with 0% and 1.3514% for assistive. These results support the choices within the tested contexts, but differences between contexts cannot be attributed to individual parameters alone.

## mission_3.error_costs

In the warehouse, nearby workers bear the risk from false safe movement, while workers and the business bear delays from unnecessary stops. From the warehouse baseline to revised attempt 4, maximum detection delay decreased from 0.10 s to 0.00 s. The false safe rate stayed at 0.6173%, the stop rate stayed at 5.6122%, and dangerous command events remained zero. In the assistive setting, the person receiving assistance bears the direct risk from unsafe movement, while unnecessary stops can interrupt access, independence, and trust. From the assistive baseline to revised attempt 3, maximum detection delay decreased from 0.05 s to 0.00 s. False safe rate remained 0%, stop rate remained 1.3514%, and dangerous command events remained zero. The revisions improved measured delay without changing the recorded error rates.

## mission_3.limitations

The seven scenarios provide repeatable evidence of how my policies respond to the simulated sensor readings and decision conditions. Both final policies recorded zero dangerous command events and 0.00 s maximum detection delay, but the warehouse policy still had a 0.6173% false safe rate. These tests do not establish safety in every environment or demonstrate that a physical robot can stop in time. Dangerous command events are a risk proxy, not actual collisions, and zero measured delay is limited by the simulation’s sampling. I would consult warehouse workers and an assistive device user with limited mobility about acceptable stopping behavior. Before deployment, I would run a controlled physical stopping distance test using a dummy obstacle, realistic operating speeds, and injected sensor dropouts to measure braking distance and response time.
