# mission_2

## comparison
At the learned acceptance threshold of 0.50, I compared normal, dim and occluded while keeping the classical settings fixed.

For normal, the classical detector had 0 correct boxes, 0 false boxes and 2 missed mugs. The learned detector had 1 correct box, 0 false boxes and 1 missed mug.

For dim, the classical detector had 0 correct boxes, 1 false box and 2 missed mugs. The learned detector had 0 correct boxes, 0 false boxes and 2 missed mugs.

For occluded, both detectors had identical results: 0 correct boxes, 0 false boxes and 2 missed mugs.

The learned detector located one additional mug under normal conditions and avoided the classical detectors false box under dim conditions. However, neither located the mugs in the dim or occluded conditions at these settings. In the paired normal_1 image, both methods show the cyan reference but no green prediction, so both miss this particular mug. The learned detectors advantage in the normal condition therefore comes from another image, not normal_1. Avoiding false boxes matters, but producing no boxes is not sufficient when the robot needs to locate the mug.

## choice
I recommend the learned detector for further testing. At the current acceptance threshold of 0.50, it found a mug under normal conditions and avoided the false detection made by the classical detector under dim conditions. However, it still missed many mugs. I would investigate a lower threshold of 0.20 next. The saved threshold sweep shows 12 correct boxes, 1 false box and 8 missed mugs across the collection, compared with 3 correct boxes, 0 false boxes and 17 missed mugs at 0.50. This trades one additional false detection for substantially fewer misses.

The learned detector took approximately 39 - 41 ms per image in the three selected conditions, compared with approximately 3.6 - 4.4 ms for the classical detector. It was slower, but its localization results justify further testing. These processing times exclude model loading and display and do not measure complete robot response time.

For normal_1, the foreground mask had IoU 0.5756 and Dice 0.7306, with 4,453 extra pixels and 1,852 missed mug pixels. This model identifies prominent foreground without assigning a cup label, so a detailed mask does not establish that the region is the requested mug. One important limitation is that this small collection contains many modified versions of the same scene, so the results do not establish performance across unfamiliar real environments.
