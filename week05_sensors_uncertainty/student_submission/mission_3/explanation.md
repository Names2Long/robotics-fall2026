# Mission 3

## Assistive.prediction_draft

Testing / debugging purposes since its not letting me continue even though I did all the necessary tests 

## Warehouse.prediction_draft

Compared with my previous weight only test, I predict that increasing the caution margin by 0.10 m will encourage earlier stops and may reduce false safe decisions. The tradeoff could be more unnecessary stops, delaying workers and deliveries.

## context_comparison

My final warehouse policy uses a stopping threshold of 0.75 m and margin of 0.20 m, giving a stop boundary of 0.95 m. My assistive policy uses a threshold of 0.95 m and margin of 0.25 m, giving a larger stop boundary of 1.20 m. This provides more distance before stopping near someone who may have difficulty moving away. Sensor A’s weight also differs, 0.50 for warehouse and 0.35 for assistive. The assistive policy relies more on steadier Sensor B, although its bias and slower updates remain limitations. Both policies recorded 0.00 s maximum detection delay and zero dangerous command events. Warehouse false safe and stop rates were 0.6173% and 5.6122%, compared with 0% and 1.3514% for assistive. These results support the choices within the tested contexts, but differences between contexts cannot be attributed to individual parameters alone.

## error_costs

In the warehouse, nearby workers bear the risk from false safe movement, while workers and the business bear delays from unnecessary stops. From the warehouse baseline to revised attempt 4, maximum detection delay decreased from 0.10 s to 0.00 s. The false safe rate stayed at 0.6173%, the stop rate stayed at 5.6122%, and dangerous command events remained zero. In the assistive setting, the person receiving assistance bears the direct risk from unsafe movement, while unnecessary stops can interrupt access, independence, and trust. From the assistive baseline to revised attempt 3, maximum detection delay decreased from 0.05 s to 0.00 s. False safe rate remained 0%, stop rate remained 1.3514%, and dangerous command events remained zero. The revisions improved measured delay without changing the recorded error rates.

## limitations

The seven scenarios provide repeatable evidence of how my policies respond to the simulated sensor readings and decision conditions. Both final policies recorded zero dangerous command events and 0.00 s maximum detection delay, but the warehouse policy still had a 0.6173% false safe rate. These tests do not establish safety in every environment or demonstrate that a physical robot can stop in time. Dangerous command events are a risk proxy, not actual collisions, and zero measured delay is limited by the simulation’s sampling. I would consult warehouse workers and an assistive device user with limited mobility about acceptable stopping behavior. Before deployment, I would run a controlled physical stopping distance test using a dummy obstacle, realistic operating speeds, and injected sensor dropouts to measure braking distance and response time.
