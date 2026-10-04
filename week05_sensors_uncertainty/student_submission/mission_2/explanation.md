# Mission 2

## comparison

At a fixed Sensor A weight of 0.25, moving average windows 3, 7, and 11 produced RMSE values of 0.1395, 0.1504, and 0.1601 m. Compared with window 3, RMSE increased by 0.0109 m for window 7 and 0.0205 m for window 11. All three had the same measured response delay of 1.10 s. For the matched window 3 comparison, median filtering slightly reduced RMSE from 0.1395 to 0.1389 m, while delay remained 1.10 s. However, maximum error increased from 1.1254 to 1.2746 m, so the median did not improve every metric.

## fusion_choice

Using median window 3 with other settings fixed, Sensor A weights of 0.25, 0.50, and 0.75 produced RMSE values of 0.1389, 0.1270, and 0.1335 m, with delays of 1.10, 0.90, and 0.45 s. Maximum errors were 1.2746, 1.4397, and 1.6049 m, respectively. I selected weight 0.50 because it gave the lowest RMSE while meeting every required limit. Compared with weight 0.25, it reduced RMSE by 0.0119 m and delay by 0.20 s. Weight 0.75 responded faster, but increased RMSE and maximum error. Sensor A is fast but noisy and prone to outliers, while Sensor B is steadier but biased and slower. Equal weighting provided a useful balance in my recorded tests.

## manual_average

4.1667

## manual_fusion

2.25

## manual_median

2.3

## prediction_draft

Compared with median window 3 at weight 0.50, increasing Sensor A’s weight to 0.75 may improve responsiveness further, but remaining noise and outliers from Sensor A could increase error.

## responsiveness

Smoothing combines recent readings to reduce fluctuations, but older readings can slow the response to a real change. In my experiments, increasing the moving average window from 3 to 7 to 11 did not change the measured sustained response delay. They all were 1.10 s. This did not support my prediction of increasing delay for these settings. With median window 3, increasing Sensor A’s weight from 0.25 to 0.50 to 0.75 reduced delay from 1.10 to 0.90 to 0.45 s. My selected configuration took 0.90 s to achieve three consecutive estimates within 0.15 m of the new truth. If a person moved closer, delayed distance estimates could postpone a robot’s stopping decision. Also, 100% availability includes held estimates and does not guarantee fresh evidence.

## selected

6
