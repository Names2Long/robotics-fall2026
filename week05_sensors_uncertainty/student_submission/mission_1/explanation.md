# Mission 1

## bias

-0.0141

## bias_vs_variance

My prediction distinguished a shift in the mean from the scattered readings. The measured mean is 1.9859 m, giving a small negative bias of −0.0141 m, while the sample variance is 0.004307 m². Bias measures how far the mean is from the true distance, while variance measures how spread out the readings are. Most readings are exactly 2.00 m or 1.90 m, suggesting coarse resolution rather than a systematic bias. The 1.10 m outlier also increases the variance.

## dropouts

6

## mean

1.9859

## median

2.0000

## more_samples

More samples would not remove the sensors coarse resolution. Out of the 234 valid readings, 209 are 2.00 m and 24 are 1.90 m, showing that measurements fall on discrete levels. More samples could make the estimated mean more stable, but that would not make individual readings more precise. The small bias of −0.0141 m does not mean the sensor can reliably distinguish distances between those levels.

## outliers

1

## prediction

I predict that a consistently biased sensor could produce readings around 2.20 m. Its mean would be above the distance of 2.00 m, giving a bias of about +0.20 m. Its variance would be low because the readings are too close together.

A noisy sensor without systematic bias would produce more scattered readings. Its mean should be close to 2.00 m and its bias close to zero, but its variance would be higher because the readings are more spread out

## prediction_draft

I predict that a consistently biased sensor could produce readings around 2.20 m. Its mean would be above the distance of 2.00 m, giving a bias of about +0.20 m. Its variance would be low because the readings are too close together.

A noisy sensor without systematic bias would produce more scattered readings. Its mean should be close to 2.00 m and its bias close to zero, but its variance would be higher because the readings are more spread out

## profile

quantized

## robot_consequence

An assistive robot might stop when its measured distance from a person falls below 1.95 m. With coarse resolution, a distance just below that threshold could round to 2.00 m, causing the robot to continue moving when it should stop. This could make the person feel unsafe or increase the risk of contact. The stopping policy should account for the sensors limited resolution

## variance

0.004307
